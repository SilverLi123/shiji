import json
import sqlite3
import shutil
import subprocess
import tempfile
import unittest
import threading
import uuid
from unittest.mock import patch

from storage import Store


class SearchIndex(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name)

    def add(self,title,**fields):
        return self.store.save({'title':title,'kind':'code',**fields})['resource']

    def matches(self,query):
        self.store.flush_search()
        from search_text import parse_terms, gram_query
        terms=parse_terms(query)
        with self.store.connect() as c:
            sql='SELECT d.id FROM search_docs d'
            params=[]
            if self.store.search_capabilities()['fts5'] and terms:
                sql+=' JOIN search_fts f ON f.rowid=d.rowid WHERE search_fts MATCH ?'
                params.append(gram_query(terms))
            else:sql+=' WHERE 1'
            for term in terms:sql+=' AND instr(d.text,?)>0';params.append(term)
            return {r[0] for r in c.execute(sql,params)}

    def test_short_chinese_mixed_code_punctuation_phrase_and_literal_operators(self):
        a=self.add('动效组件 React Motion',snippet='foo::bar C++ useState',tags=['New, exact'])
        b=self.add('Motion React 说明',notes='设计灵感',description='literal OR NOT * \\ "quoted"')
        for text,expected in [('动',{a['id']}),('动效',{a['id']}),('react 动效',{a['id']}),
            ('"React Motion"',{a['id']}),('foo::bar C++',{a['id']}),('New, exact',{a['id']}),
            ('OR NOT',{b['id']}),('*',{b['id']}),('\\',{b['id']}),('',{a['id'],b['id']})]:
            with self.subTest(text=text):self.assertEqual(self.matches(text),expected)

    def test_all_text_fields_attachments_and_direct_sql_updates(self):
        a=self.add('开始',projectNotes={'旧项目':'历史项目备注'},snippet='提示词内容')
        self.store.attachment(a['id'],b'ID3test',{'name':'音效附件.mp3','author':'Attachment Author','sourceUrl':'https://assets.example.org/'})
        for q in ('历史项目','提示词','音效附件','Attachment Author','assets.example.org'):
            self.assertEqual(self.matches(q),{a['id']})
        with self.store.connect() as c:
            value=json.loads(c.execute('SELECT payload FROM resources WHERE id=?',(a['id'],)).fetchone()[0]);value['title']='直接同步写入'
            c.execute('UPDATE resources SET payload=? WHERE id=?',(json.dumps(value),a['id']))
        self.assertEqual(self.matches('直接同步'),{a['id']})
        self.assertEqual(self.matches('开始'),set())
        aid=self.store.get(a['id'])['attachments'][0]['id']
        self.store.update_attachment(aid,{'author':'New Author'})
        self.assertEqual(self.matches('New Author'),{a['id']})
        self.assertEqual(self.matches('Attachment Author'),set())

    def test_restart_missing_index_and_corruption_rebuild_preserve_resources(self):
        a=self.add('重建 中文')
        before=self.store.get(a['id'])
        self.assertEqual(self.matches('重建'),{a['id']})
        with self.store.connect() as c:c.execute('DROP TABLE search_fts')
        self.store=Store(self.temp.name)
        self.assertEqual(self.matches('中文'),{a['id']})
        with self.store.connect() as c:c.execute('DELETE FROM search_docs')
        self.store.rebuild_search()
        self.assertEqual(self.matches('重建'),{a['id']})
        self.assertEqual(self.store.get(a['id']),before)
        with self.store.connect() as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)

    def test_upsert_sync_and_restore_with_already_dirty_id(self):
        a=self.add('Original')
        with self.store.connect() as c:
            row=c.execute('SELECT * FROM resources WHERE id=?',(a['id'],)).fetchone()
            for title in ('Phone edit','Restored edit'):
                payload=json.loads(row['payload']);payload['title']=title
                c.execute('INSERT INTO resources VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(a['id'],row['url'],json.dumps(payload),0))
        self.assertEqual(self.matches('Restored edit'),{a['id']})

    @unittest.skipUnless(shutil.which('sqlite3'),'SQLite CLI needed only to simulate protected FTS shadow corruption')
    def test_runtime_fts_shadow_damage_repairs_only_disposable_data(self):
        a=self.add('中文动效');self.store.flush_search();before=self.store.get(a['id'])
        subprocess.run(['sqlite3',str(self.store.db)],input='.dbconfig defensive off\nPRAGMA writable_schema=ON;\nDELETE FROM search_fts_data WHERE id>10;\n',text=True,capture_output=True,check=True)
        self.assertEqual(self.store.get(a['id']),before)
        self.assertEqual(self.store.query_resources({'filters':{'search':'动效'}})['total'],1)
        self.assertEqual(self.store.get(a['id']),before)

    def test_no_fts_runtime_keeps_exact_results(self):
        self.add('两字 中文 C++')
        expected=self.matches('两字 C++')
        with patch('search_index.probe_fts',return_value=False):
            other=Store(self.temp.name)
            self.assertFalse(other.search_capabilities()['fts5'])
            self.store=other
            self.assertEqual(self.matches('两字 C++'),expected)

    def test_legacy_state_reads_attachments_in_batches(self):
        for i in range(20):
            a=self.add('Title '+str(i))
            self.store.attachment(a['id'],b'ID3data',{'name':'a.mp3'})
        original=self.store.connect;queries=[]
        def connect():
            c=original();c.set_trace_callback(queries.append);return c
        with patch.object(self.store,'connect',side_effect=connect):
            state=self.store.state()
        self.assertEqual(len(state['resources']),20)
        self.assertTrue(all(len(r['attachments'])==1 for r in state['resources']))
        reads=[q for q in queries if q.lstrip().upper().startswith('SELECT') and 'FROM attachments' in q]
        self.assertLessEqual(len(reads),2,'Full export must not execute one attachment lookup per resource')

    def test_background_accelerator_fallback_is_complete_and_becomes_indexed(self):
        with self.store.connect() as c:
            for i in range(300):self.store._write(c,{'title':'后台中文 '+str(i),'kind':'code'})
        with patch.object(self.store,'_schedule_fts'):
            page=self.store.query_resources({'filters':{'search':'中文'},'limit':1})
            self.assertEqual(page['total'],300)
            self.assertTrue(self.store.search_capabilities()['indexing'])
            self.store.save({'title':'人工改名'},page['resources'][0]['id'])
            self.assertEqual(self.store.query_resources({'filters':{'search':'中文'}})['total'],299)
        self.store.flush_search()
        self.assertFalse(self.store.search_capabilities()['indexing'])
        self.assertEqual(self.store.query_resources({'filters':{'search':'中文'}})['total'],299)

    def test_import_restore_and_phone_sync_reindex_real_business_writes(self):
        original=self.add('备份搜索原文',notes='完整人工备注')
        self.matches('原文')
        backup=self.store.backup_bytes()
        self.store.save({'title':'改名'},original['id'])
        self.assertEqual(self.matches('原文'),set())
        with tempfile.TemporaryDirectory() as target:
            restored=Store(target)
            try:
                restored.restore_zip(backup)
                self.assertEqual(restored.query_resources({'filters':{'search':'备份搜索原文'}})['total'],1)
                self.assertEqual(restored.get(original['id'])['notes'],'完整人工备注')
            finally:restored.stop_search_worker()
        self.store.import_json({'version':1,'resources':[{'title':'导入检索词','kind':'code','snippet':'完整导入代码'}]})
        self.assertEqual(len(self.matches('导入检索词')),1)
        from mobile_sync import SyncEngine
        engine=SyncEngine(self.store);snapshot=engine.snapshot()
        resource={**self.store.get(original['id']),'title':'手机修改后的检索词'}
        engine.commit({'version':1,'libraryId':snapshot['libraryId'],'expectedRevision':snapshot['revision'],'requestId':str(uuid.uuid4()),'resources':[resource]})
        self.assertEqual(self.matches('手机修改后的检索词'),{original['id']})

    def test_capture_in_flight_search_and_late_metadata_incremental_update(self):
        from quick_capture import fallback_title
        r=self.store.save({'title':fallback_title('https://example.com/capture'),'url':'https://example.com/capture','inbox':True})['resource']
        started=threading.Event();release=threading.Event();errors=[]
        def fetch(*args):
            started.set()
            if not release.wait(3):raise RuntimeError('fixture was not released')
            return {'metadata':{'title':'自动补全搜索测试','description':'可检索的真实补全字段'}}
        def run():
            try:self.store.capture_step()
            except Exception as e:errors.append(e)
        with patch('capture_jobs.fetch_payload',side_effect=fetch):
            thread=threading.Thread(target=run);thread.start()
            try:
                self.assertTrue(started.wait(2))
                self.assertEqual(self.store.query_resources({'filters':{'search':'example.com'}})['total'],1)
                self.store.save({'notes':'人工编辑不被覆盖'},r['id'])
            finally:release.set();thread.join(4)
        self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
        self.assertEqual(self.store.get(r['id'])['notes'],'人工编辑不被覆盖')
        self.assertEqual(self.store.query_resources({'filters':{'search':'人工编辑不被覆盖'}})['total'],1)

    def test_transaction_context_releases_connection(self):
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT 1').fetchone()[0],1)
        with self.assertRaises(sqlite3.ProgrammingError):c.execute('SELECT 1')

    def test_invalid_query_and_safe_codepoint_highlight(self):
        from search_text import parse_terms, highlight_ranges
        for text in (None,123,'x'*201,'\ud800'):
            with self.assertRaises(ValueError):parse_terms(text)
        self.assertEqual(parse_terms('  "React Motion"   动效 '),['react motion','动效'])
        self.assertEqual(highlight_ranges('🙂动效 <script>React</script>',['动效','react']),[[1,3],[12,17]])


if __name__=='__main__':unittest.main()
