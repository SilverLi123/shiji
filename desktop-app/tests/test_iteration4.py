import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
import test_upgrade as fixture

class Iteration4(unittest.TestCase):
    setUp=fixture.Integration.setUp
    start=fixture.Integration.start
    tearDown=fixture.Integration.tearDown
    req=fixture.Integration.req
    add=fixture.Integration.add
    def project(self,name,**values):return self.req('/api/collections','POST',{'name':name,**values})
    def test_hierarchy_rules_and_batch_add_apply_only_new_membership(self):
        self.project('游戏',autoTags=['游戏']);self.project('界面',parent='游戏',autoTags=['UI'])
        a=self.add(projects=['界面'],tags=['手动']);self.assertEqual(a['tags'],['手动','UI','游戏'])
        edited=self.req('/api/resources/'+a['id'],'PUT',{**a,'tags':['手动']})['resource'];self.assertEqual(edited['tags'],['手动'])
        b=self.add(url='https://b.example/');self.req('/api/batch','POST',{'ids':[b['id']],'action':'projects','projects':['界面']})
        self.assertEqual(next(r for r in self.req('/api/resources')['resources'] if r['id']==b['id'])['tags'],['UI','游戏'])
    def test_project_rename_updates_notes_trash_children_and_smart_filter(self):
        self.project('游戏');self.project('音效',parent='游戏');r=self.add(projects=['游戏'],projectNotes={'游戏':'note'});self.req('/api/resources/'+r['id'],'DELETE')
        self.req('/api/smart-collections','POST',{'name':'游戏智能','filters':{'collection':'游戏'}})
        self.req('/api/collections/update','POST',{'original':'游戏','name':'原型','parent':'','autoTags':[],'archived':False})
        state=self.req('/api/resources');self.assertEqual(next(p for p in state['collectionMeta'] if p['name']=='音效')['parent'],'原型')
        self.assertEqual(state['smartCollections'][0]['filters']['collection'],'原型');r=self.req('/api/trash')['resources'][0];self.assertEqual(r['projectNotes'],{'原型':'note'})
    def test_tag_merge_updates_auto_rules_and_future_resources(self):
        self.project('参考',autoTags=['旧','新']);self.project('下级',parent='参考',autoTags=['旧'])
        first=self.add(projects=['下级'])
        self.req('/api/tags','POST',{'from':'旧','to':'新'})
        state=self.req('/api/resources')
        self.assertEqual(next(r for r in state['resources'] if r['id']==first['id'])['tags'],['新'])
        self.assertTrue(all(p['autoTags']==['新'] for p in state['collectionMeta']))
        self.assertEqual(self.add(url='https://later.example/',projects=['下级'])['tags'],['新'])
    def test_project_cycle_collision_and_tag_overflow_are_atomic(self):
        self.project('A');self.project('B',parent='A');a=self.add(projects=['A'],tags=['t'+str(i) for i in range(30)])
        self.req('/api/collections/update','POST',{'original':'A','name':'A','parent':'B'},status=400)
        self.req('/api/collections/update','POST',{'original':'A','name':'B','parent':''},status=409)
        self.req('/api/collections/update','POST',{'original':'A','name':'A','parent':'','autoTags':['extra'],'applyExisting':True},status=400)
        meta={p['name']:p for p in self.req('/api/resources')['collectionMeta']};self.assertEqual(meta['A']['parent'],'');self.assertEqual(meta['A']['autoTags'],[])
    def test_archive_is_reversible_and_does_not_remove_resources(self):
        self.project('A');self.project('B',parent='A');r=self.add(projects=['B'])
        self.req('/api/collections/update','POST',{'original':'A','name':'A','parent':'','archived':True})
        state=self.req('/api/resources');self.assertEqual(len(state['resources']),1);self.assertTrue(next(p for p in state['collectionMeta'] if p['name']=='A')['archived'])
        self.req('/api/collections/update','POST',{'original':'A','name':'A','parent':'','archived':False})
        self.assertEqual(self.req('/api/resources')['resources'][0]['id'],r['id'])
    def test_moving_project_preserves_membership_and_rejects_deep_tree(self):
        self.project('A');self.project('B');self.project('C',parent='A');r=self.add(projects=['C'])
        self.req('/api/collections/update','POST',{'original':'C','name':'C','parent':'B'})
        self.assertEqual(next(p for p in self.req('/api/resources')['collectionMeta'] if p['name']=='C')['parent'],'B')
        self.assertEqual(self.req('/api/resources')['resources'][0]['id'],r['id'])
        parent='B'
        for i in range(9):name='nested'+str(i);self.project(name,parent=parent);parent=name
        self.req('/api/collections','POST',{'name':'tooDeep','parent':parent},status=400)
        self.assertNotIn('tooDeep',self.req('/api/resources')['collections'])
    def test_folder_metadata_backup_json_and_zip_roundtrip(self):
        self.project('A',autoTags=['tag']);self.project('B',parent='A');self.add(projects=['B']);export=self.req('/api/export');backup=self.req('/api/backup.zip')
        with tempfile.TemporaryDirectory() as d:
            import sys;sys.path.insert(0,str(fixture.APP));from storage import Store
            for kind in ['json','zip']:
                other=Store(Path(d)/kind)
                if kind=='json':other.import_json(export)
                else:other.restore_zip(backup)
                self.assertEqual(other.state()['collectionMeta'],export['collectionMeta'])
    def test_invalid_backup_tree_rejected_before_mutation(self):
        self.project('A');blob=self.req('/api/backup.zip');out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(blob)) as z,zipfile.ZipFile(out,'w') as w:
            m=json.loads(z.read('manifest.json'));m['collectionMeta']=[{'name':'A','parent':'A','autoTags':[],'archived':False}]
            for name in z.namelist():w.writestr(name,json.dumps(m) if name=='manifest.json' else z.read(name))
        self.req('/api/restore','POST',raw=out.getvalue(),status=400)
        self.assertEqual(self.req('/api/resources')['collectionMeta'][0]['parent'],'')
    def test_link_preview_classifies_duplicates_and_import_is_atomic(self):
        old=self.add();deleted=self.add(url='https://trash.example/',notes='keep');self.req('/api/resources/'+deleted['id'],'DELETE')
        p=self.req('/api/links/preview','POST',{'text':'https://example.com/#fragment\nhttps://new.example/\nhttps://NEW.example:443/\nnot a url\nhttps://trash.example/\n[React](https://react.example/)'} )
        self.assertEqual([x['status'] for x in p['items']],['existing','new','duplicate','invalid','trash','new'])
        self.req('/api/links/import','POST',{'items':[{'url':'https://atomic.example/','title':'ok'},{'url':'javascript:alert(1)','title':'bad'}]},status=400)
        self.assertEqual(len(self.req('/api/resources')['resources']),1)
        self.project('参考',autoTags=['自动'])
        result=self.req('/api/links/import','POST',{'items':[x for x in p['items'] if x['status']!='invalid'],'projects':['参考'],'tags':['手动']})
        self.assertEqual(result['added'],2);self.assertEqual(result['skipped'],3)
        rows=self.req('/api/resources')['resources'];self.assertEqual(next(r for r in rows if r['url']=='https://react.example/')['title'],'React')
        self.assertEqual(next(r for r in rows if r['url']=='https://new.example/')['tags'],['手动','自动']);self.assertEqual(self.req('/api/trash')['resources'][0]['notes'],'keep')
    def test_v2_migration_preserves_flat_project_and_original_resource(self):
        r=self.add(projects=['旧项目'],projectNotes={'旧项目':'用途'})
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close()
        with sqlite3.connect(Path(self.temp.name)/'library.sqlite3') as c:
            c.execute('DROP TABLE collections');c.execute('CREATE TABLE collections(name TEXT PRIMARY KEY)');c.execute('INSERT INTO collections VALUES(?)',('旧项目',));c.execute('PRAGMA user_version=2')
        self.start();state=self.req('/api/resources');self.assertEqual(state['resources'][0]['id'],r['id']);self.assertEqual(state['resources'][0]['projectNotes'],{'旧项目':'用途'})
        self.assertEqual(state['collectionMeta'],[{'name':'旧项目','parent':'','autoTags':[],'archived':False}]);self.assertTrue((Path(self.temp.name)/'before-folders.sqlite3').exists())
