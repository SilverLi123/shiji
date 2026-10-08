import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store

class QuickProjects(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def resource(self,title='Resource',projects=None):
        return self.store.save({'kind':'file','title':title,'projects':projects or [],'projectNotes':{n:'Existing note '+n for n in (projects or [])},'tags':['old'],'notes':'Keep notes','author':'Original author','sourceUrl':'https://example.com/source','license':'待确认'})['resource']
    def test_additive_membership_exact_names_inherited_tags_and_noop(self):
        self.store.collection('Original');self.store.collection('Parent',auto_tags=['inherited']);self.store.collection('Design & sound',parent='Parent',auto_tags=['direct'])
        r=self.resource(projects=['Original']);a=self.store.attachment(r['id'],fixture.PNG,{'name':'Image.png','author':'Asset author','license':'待确认'})['attachment'];before=self.store.get(r['id'])
        result=self.store.assign_projects({'ids':[r['id'],r['id']],'projects':['Design & sound']});self.assertEqual(result['changed'],1)
        after=self.store.get(r['id']);self.assertEqual(after['projects'],['Original','Design & sound']);self.assertEqual(set(after['tags']),{'old','direct','inherited'})
        for key in ['id','title','notes','author','sourceUrl','license','attachments','coverId','createdAt']:self.assertEqual(after[key],before[key],key)
        self.assertEqual(after['projectNotes']['Original'],'Existing note Original');self.assertEqual((self.store.files/a['id']).read_bytes(),fixture.PNG)
        second=self.store.assign_projects({'ids':[r['id']],'projects':['Design & sound']});self.assertEqual(second['changed'],0);self.assertEqual(self.store.get(r['id']),after)
    def test_invalid_removed_archived_and_trashed_targets_leave_full_state(self):
        self.store.collection('Open');self.store.collection('Hidden');self.store.update_collection({'original':'Hidden','archived':True});self.store.collection('Child',parent='Hidden')
        active=self.resource();trash=self.resource('Trash');self.store.remove(trash['id']);before=self.store.state();trashed=self.store.state(trash=True)
        for body in [{'ids':[active['id']],'projects':['Unknown']},{'ids':[active['id']],'projects':['Child']},{'ids':[trash['id']],'projects':['Open']},{'ids':[active['id'],'missing'],'projects':['Open']},{'ids':[],'projects':['Open']},{'ids':[active['id']],'projects':[]},{'ids':[active['id']],'projects':['Open'],'other':True}]:
            with self.subTest(body=body),self.assertRaises(ValueError):self.store.assign_projects(body)
            self.assertEqual(self.store.state(),before);self.assertEqual(self.store.state(trash=True),trashed)
    def test_batch_limit_failure_rolls_back_earlier_items(self):
        projects=['P'+str(i) for i in range(31)]
        for name in projects:self.store.collection(name)
        a=self.resource('A');b=self.resource('B',projects[:30]);before=self.store.state()
        with self.assertRaises(ValueError):self.store.assign_projects({'ids':[a['id'],b['id']],'projects':[projects[-1]]})
        self.assertEqual(self.store.state(),before)
    def test_batch_write_failure_rolls_back_and_stale_name_is_not_recreated(self):
        self.store.collection('Chosen');a=self.resource('A');b=self.resource('B');before=self.store.state();write=self.store._write;calls=0
        def failing(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise RuntimeError('injected failure')
            return write(*args,**kwargs)
        with patch.object(self.store,'_write',side_effect=failing),self.assertRaises(RuntimeError):self.store.assign_projects({'ids':[a['id'],b['id']],'projects':['Chosen']})
        self.assertEqual(self.store.state(),before)
        self.store.update_collection({'original':'Chosen','name':'Renamed'});before=self.store.state()
        with self.assertRaises(ValueError):self.store.assign_projects({'ids':[a['id']],'projects':['Chosen']})
        self.assertEqual(self.store.state(),before)

class QuickProjectsHTTP(unittest.TestCase):
    setUp=fixture.Integration.setUp;tearDown=fixture.Integration.tearDown;start=fixture.Integration.start;req=fixture.Integration.req;add=fixture.Integration.add
    def test_real_endpoint_adds_only_projects_and_enforces_origin(self):
        r=self.add();self.req('/api/collections','POST',{'name':'Exact & name'})
        result=self.req('/api/projects/assign','POST',{'ids':[r['id']],'projects':['Exact & name']});self.assertEqual(result['changed'],1)
        after=next(x for x in self.req('/api/resources')['resources'] if x['id']==r['id']);self.assertEqual(after['projects'],['Exact & name'])
        for key in ['title','notes','license','sourceUrl']:self.assertEqual(after[key],r[key])
        self.req('/api/projects/assign','POST',{'ids':[r['id']],'projects':['missing']},status=400)
        self.req('/api/projects/assign','POST',{'ids':[r['id']],'projects':['Exact & name']},status=403,headers={'Origin':'https://evil.example'})
