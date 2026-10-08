import tempfile
import unittest
from pathlib import Path
import test_upgrade as fixture

class SmartFilters(unittest.TestCase):
    setUp=fixture.Integration.setUp
    start=fixture.Integration.start
    tearDown=fixture.Integration.tearDown
    req=fixture.Integration.req
    add=fixture.Integration.add
    def test_update_preserves_id_and_resource_payload(self):
        resource=self.add();s=self.req('/api/smart-collections','POST',{'name':'原名称','filters':{'tags':['React']}})
        updated=self.req('/api/smart-collections/'+s['id'],'PUT',{'name':'新名称','filters':{'tagMode':'any','tags':['React','设计'],'excludeTags':['弃用'],'favorite':False,'domain':'REACTBITS.DEV.'}})
        self.assertEqual(updated['id'],s['id']);self.assertEqual(updated['name'],'新名称');self.assertFalse(updated['filters']['favorite'])
        self.assertEqual(updated['filters']['domain'],'reactbits.dev')
        state=self.req('/api/resources');self.assertEqual(state['resources'],[resource]);self.assertEqual(len(state['smartCollections']),1)
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close();self.start()
        self.assertEqual(self.req('/api/resources')['smartCollections'][0],updated)
    def test_missing_id_not_recreated_and_invalid_update_atomic(self):
        s=self.req('/api/smart-collections','POST',{'name':'保留','filters':{}});before=self.req('/api/resources')
        self.req('/api/smart-collections/missing','PUT',{'name':'新','filters':{}},status=404)
        for filters in [{'tagMode':'bad'},{'createdFrom':'2025-02-29'},{'createdFrom':'2026-10-02','createdTo':'2026-10-01'},{'domain':'https://example.com/'},{'includeSubdomains':'true'},{'mediaType':'zip'},{'noTags':1},{'excludeTags':['x'*51]}]:
            self.req('/api/smart-collections/'+s['id'],'PUT',{'name':'不应保存','filters':filters},status=400)
            self.assertEqual(self.req('/api/resources'),before)
    def test_filter_validation_readonly_defaults_and_idna(self):
        before=self.req('/api/resources')
        result=self.req('/api/filters/validate','POST',{'filters':{'domain':'例子.测试','createdFrom':'2024-02-29','inbox':False}})['filters']
        self.assertEqual(result['domain'],'xn--fsqu00a.xn--0zwm56d');self.assertEqual(result['tagMode'],'all');self.assertTrue(result['includeSubdomains']);self.assertFalse(result['inbox'])
        for domain in ['example.com:443','user@example.com','*.example.com','bad..example.com','-bad.example','a/' ]:self.req('/api/filters/validate','POST',{'filters':{'domain':domain}},status=400)
        self.assertEqual(self.req('/api/resources'),before)
    def test_excluded_tag_rename_merge_and_project_rename(self):
        self.req('/api/collections','POST',{'name':'项目'})
        self.add(tags=['旧','其他'],projects=['项目'])
        s=self.req('/api/smart-collections','POST',{'name':'规则','filters':{'tags':['旧','新'],'excludeTags':['旧','新'],'collection':'项目'}})
        self.req('/api/tags','POST',{'from':'旧','to':'新'})
        self.req('/api/collections/update','POST',{'original':'项目','name':'新项目','parent':''})
        rule=self.req('/api/resources')['smartCollections'][0]['filters'];self.assertEqual(rule['tags'],['新']);self.assertEqual(rule['excludeTags'],['新']);self.assertEqual(rule['collection'],'新项目')
    def test_international_domain_cannot_silently_change_identity(self):
        before=self.req('/api/resources')
        for domain in ['faß.de','straße.de','ς.gr','a\u200db.example']:
            result=self.req('/api/filters/validate','POST',{'filters':{'domain':domain}},status=400)
            self.assertIn('error',result)
        for domain in ['xn--fa-hia.de','fass.de','xn--strae-oqa.de','strasse.de']:
            result=self.req('/api/filters/validate','POST',{'filters':{'domain':domain}})['filters']
            self.assertEqual(result['domain'],domain)
        self.assertEqual(self.req('/api/resources'),before)
    def test_advanced_conditions_json_and_zip_roundtrip(self):
        filters={'tags':['A','B'],'tagMode':'any','excludeTags':['C'],'domain':'example.com','includeSubdomains':False,'createdFrom':'2024-02-29','createdTo':'2026-10-02','favorite':False,'inbox':True,'hasNotes':True,'noTags':False,'noProjects':True,'mediaType':'audio','color':'#268bd2'}
        s=self.req('/api/smart-collections','POST',{'name':'完整规则','filters':filters});export=self.req('/api/export');backup=self.req('/api/backup.zip')
        import sys;sys.path.insert(0,str(fixture.APP));from storage import Store
        with tempfile.TemporaryDirectory() as d:
            for kind in ['json','zip']:
                other=Store(Path(d)/kind)
                if kind=='json':other.import_json(export)
                else:other.restore_zip(backup)
                restored=other.state()['smartCollections'][0]
                self.assertEqual(restored['name'],s['name']);self.assertEqual(restored['filters'],s['filters'])
    def test_legacy_stored_filters_read_without_rewrite(self):
        import sqlite3,json
        old={'search':'UI','tags':['开发'],'favorite':False}
        with sqlite3.connect(Path(self.temp.name)/'library.sqlite3') as db:db.execute('INSERT INTO smart_collections VALUES(?,?,?)',('legacy','旧规则',json.dumps(old)))
        self.assertEqual(self.req('/api/resources')['smartCollections'][0]['filters'],old)
        normal=self.req('/api/filters/validate','POST',{'filters':old})['filters'];self.assertEqual(normal['tags'],['开发']);self.assertEqual(normal['tagMode'],'all');self.assertFalse(normal['favorite'])
        self.assertEqual(self.req('/api/resources')['smartCollections'][0]['filters'],old)
