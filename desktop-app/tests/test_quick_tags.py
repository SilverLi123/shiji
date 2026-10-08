import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store

class QuickTags(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def resource(self,title='Resource',tags=None):
        return self.store.save({'kind':'file','title':title,'tags':tags or [],'notes':'Original notes','author':'Original author','sourceUrl':'https://example.com/source','license':'待确认','projects':['Existing project'],'projectNotes':{'Existing project':'Project note'}})['resource']
    def assign(self,ids,tags=None,create=None):return self.store.assign_tags({'ids':ids,'tags':tags or [],'create':create or []})
    def test_add_exact_names_preserve_all_other_fields_and_noop(self):
        donor=self.resource('Donor',['UI, design','ui']);r=self.resource(tags=['old','UI'])
        a=self.store.attachment(r['id'],fixture.PNG,{'name':'Original.png','author':'Asset author','sourceUrl':'https://example.com/asset','license':'待确认','cover':True})['attachment'];before=self.store.get(r['id'])
        result=self.assign([r['id'],r['id']],['UI, design','ui'],['new & <tag>','💡'*50]);self.assertEqual(result['changed'],1)
        after=self.store.get(r['id']);self.assertEqual(after['tags'],['old','UI','UI, design','ui','new & <tag>','💡'*50])
        for key in before:
            if key not in ('tags','updatedAt'):self.assertEqual(after[key],before[key],key)
        self.assertEqual((self.store.files/a['id']).read_bytes(),fixture.PNG);self.assertEqual(self.store.get(donor['id']),donor)
        self.assertEqual(self.assign([r['id']],['UI, design','ui'],['new & <tag>'])['changed'],0);self.assertEqual(self.store.get(r['id']),after)
    def test_stale_existing_labels_do_not_recreate_but_explicit_creation_is_allowed(self):
        donor=self.resource('Donor',['old tag']);target=self.resource();self.store.rename_tag('old tag','renamed');before=self.store.state()
        with self.assertRaisesRegex(ValueError,'标签已变化'):self.assign([target['id']],['old tag'])
        self.assertEqual(self.store.state(),before)
        self.assertEqual(self.assign([target['id']],create=['renamed'])['changed'],1)
        self.assertEqual(self.assign([target['id']],create=['old tag'])['changed'],1)
    def test_trash_only_labels_and_targets_and_missing_targets_rejected(self):
        donor=self.resource('Trash donor',['only trash']);target=self.resource();self.store.remove(donor['id']);before=self.store.state();trash=self.store.state(True)
        for ids,tags,create in [([target['id']],['only trash'],[]),([target['id'],'missing'],[],['new']),([target['id'],donor['id']],[],['new'])]:
            with self.subTest(ids=ids),self.assertRaises(ValueError):self.assign(ids,tags,create)
            self.assertEqual(self.store.state(),before);self.assertEqual(self.store.state(True),trash)
    def test_invalid_body_and_combined_limit_do_not_write(self):
        r=self.resource();before=self.store.state()
        bodies=[None,[],{}, {'ids':[],'tags':[],'create':['new']},{'ids':[r['id']],'tags':[],'create':[]},{'ids':'bad','tags':[],'create':['new']},{'ids':['../../x'],'tags':[],'create':['new']},{'ids':[r['id']],'tags':[],'create':['x'*51]},{'ids':[r['id']],'tags':[],'create':['💡'*51]},{'ids':[r['id']],'tags':[],'create':[' ']},{'ids':[r['id']],'tags':[],'create':['new'],'other':True},{'ids':[r['id']],'tags':['t'+str(i) for i in range(20)],'create':['c'+str(i) for i in range(20)]}]
        for body in bodies:
            with self.subTest(body=body),self.assertRaises((ValueError,TypeError)):self.store.assign_tags(body)
            self.assertEqual(self.store.state(),before)
    def test_limit_and_injected_write_failure_roll_back_whole_batch_and_dirty(self):
        a=self.resource('First');b=self.resource('Full',['t'+str(i) for i in range(30)]);before=self.store.state();self.store.dirty=False
        with self.assertRaises(ValueError):self.assign([a['id'],b['id']],create=['new'])
        self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
        original=self.store._write;calls=[]
        def failing(*args,**kwargs):
            calls.append(True)
            if len(calls)==2:raise RuntimeError('second write failed')
            return original(*args,**kwargs)
        c=self.resource('Second');before=self.store.state();self.store.dirty=False
        with patch.object(self.store,'_write',side_effect=failing),self.assertRaisesRegex(RuntimeError,'second write'):self.assign([a['id'],c['id']],create=['new'])
        self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
    def test_latest_metadata_and_removed_auto_tags_are_preserved(self):
        r=self.resource();self.store.update_collection({'original':'Existing project','autoTags':['automatic']})
        latest=self.store.save({'notes':'Concurrent new note','favorite':True},r['id'])['resource']
        self.assign([r['id']],create=['chosen']);after=self.store.get(r['id'])
        self.assertEqual(after['tags'],['chosen']);self.assertEqual(after['notes'],latest['notes']);self.assertTrue(after['favorite'])
        self.assertEqual(after['projectNotes'],latest['projectNotes'])

class QuickTagsHTTP(unittest.TestCase):
    setUp=fixture.Integration.setUp
    start=fixture.Integration.start
    tearDown=fixture.Integration.tearDown
    req=fixture.Integration.req
    def test_tag_assignment_endpoint_and_origin(self):
        r=self.req('/api/resources','POST',{'kind':'file','title':'Target','notes':'Keep this','license':'待确认'})['resource']
        result=self.req('/api/tags/assign','POST',{'ids':[r['id']],'tags':[],'create':['A, B']});self.assertEqual(result['changed'],1)
        after=self.req('/api/resources')['resources'][0];self.assertEqual(after['tags'],['A, B']);self.assertEqual(after['notes'],'Keep this')
        self.req('/api/tags/assign','POST',{'ids':[r['id']],'tags':['missing'],'create':[]},status=400)
        self.req('/api/tags/assign','POST',{'ids':[r['id']],'tags':[],'create':['C']},status=403,headers={'Origin':'https://evil.example'})
