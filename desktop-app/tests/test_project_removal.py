import sys,tempfile,unittest
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store,validate

class ProjectRemoval(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def resource(self,title='Resource',projects=None):
        return self.s.save({'kind':'file','title':title,'projects':projects or ['Parent','Child','Other'],'projectNotes':{p:'Original note '+p for p in (projects or ['Parent','Child','Other'])},'tags':['keep'],'notes':'Resource note','author':'Author','sourceUrl':'https://example.com/source','license':'待确认'})['resource']
    def setup_tree(self):
        self.s.collection('Parent');self.s.collection('Child',parent='Parent');self.s.collection('Other')
    def remove(self,ids,projects):return self.s.remove_projects({'ids':ids,'projects':projects})
    def test_exact_removal_keeps_child_other_metadata_and_archived_notes(self):
        self.setup_tree();r=self.resource();a=self.s.attachment(r['id'],fixture.PNG,{'name':'Original.png','author':'Asset author','license':'待确认','cover':True})['attachment'];before=self.s.get(r['id'])
        self.s.update_collection({'original':'Other','archived':True});self.assertEqual(self.remove([r['id'],r['id']],['Parent','Other'])['changed'],1)
        after=self.s.get(r['id']);self.assertEqual(after['projects'],['Child']);self.assertEqual(after['collection'],'Child')
        for k in before:
            if k not in ('projects','collection','updatedAt'):self.assertEqual(before[k],after[k],k)
        self.assertEqual((self.s.files/a['id']).read_bytes(),fixture.PNG)
        self.s.dirty=False;self.assertEqual(self.remove([r['id']],['Other'])['changed'],0);self.assertEqual(self.s.get(r['id']),after);self.assertFalse(self.s.dirty)
    def test_full_edit_and_rejoin_restore_notes_with_current_auto_tags(self):
        self.setup_tree();r=self.resource();after=self.s.save({'projects':[],'projectNotes':{}},r['id'])['resource'];self.assertEqual(after['projectNotes'],r['projectNotes']);self.assertEqual(after['collection'],'')
        self.s.update_collection({'original':'Parent','autoTags':['current auto']});self.s.assign_projects({'ids':[r['id']],'projects':['Parent']});joined=self.s.get(r['id']);self.assertEqual(joined['projectNotes'],r['projectNotes']);self.assertEqual(joined['tags'],['keep','current auto'])
        cleared=self.s.save({'projectNotes':{'Parent':''}},r['id'])['resource'];self.assertEqual(cleared['projectNotes']['Parent'],'');self.assertEqual(cleared['projectNotes']['Child'],r['projectNotes']['Child'])
    def test_rename_historical_notes_in_active_and_trash_and_collision_rollback(self):
        self.setup_tree();a=self.resource('A');b=self.resource('B');self.remove([a['id'],b['id']],['Parent']);self.s.remove(b['id']);self.s.update_collection({'original':'Parent','name':'Renamed'})
        for rid in (a['id'],b['id']):
            r=self.s.get(rid);self.assertNotIn('Parent',r['projectNotes']);self.assertEqual(r['projectNotes']['Renamed'],'Original note Parent');self.assertNotIn('Renamed',r['projects'])
        self.s.save({'projectNotes':{'Collision':'Conflicting note'}},a['id']);before=self.s.state();trash=self.s.state(True)
        with self.assertRaisesRegex(ValueError,'备注冲突'):self.s.update_collection({'original':'Renamed','name':'Collision'})
        self.assertEqual(self.s.state(),before);self.assertEqual(self.s.state(True),trash)
    def test_retained_notes_json_and_complete_zip_roundtrip(self):
        self.setup_tree();r=self.resource();a=self.s.attachment(r['id'],fixture.PNG,{'name':'Source.png','license':'待确认'})['attachment'];self.remove([r['id']],['Parent','Child','Other']);saved=self.s.get(r['id'])
        with tempfile.TemporaryDirectory() as d:
            other=Store(d);other.import_json(self.s.export());copy=other.state()['resources'][0];self.assertEqual(copy['projectNotes'],saved['projectNotes']);self.assertEqual(copy['projects'],[])
        with tempfile.TemporaryDirectory() as d:
            other=Store(d);other.restore_zip(self.s.backup_bytes());copy=other.get(r['id']);self.assertEqual(copy['projectNotes'],saved['projectNotes']);self.assertEqual(copy['projects'],[]);self.assertEqual((other.files/a['id']).read_bytes(),fixture.PNG)
    def test_validation_stale_trash_and_second_write_rollback(self):
        self.setup_tree();a=self.resource('A');b=self.resource('B');trash=self.resource('Trash');self.s.remove(trash['id']);before=self.s.state();trashed=self.s.state(True)
        for body in [None,{}, {'ids':[],'projects':['Parent']},{'ids':[a['id']],'projects':[]},{'ids':[a['id']],'projects':['missing']},{'ids':[a['id'],trash['id']],'projects':['Parent']},{'ids':[a['id'],'missing'],'projects':['Parent']},{'ids':[a['id']],'projects':['Parent'],'other':True}]:
            with self.subTest(body=body),self.assertRaises((ValueError,TypeError)):self.s.remove_projects(body)
            self.assertEqual(self.s.state(),before);self.assertEqual(self.s.state(True),trashed)
        original=self.s._write;calls=[];self.s.dirty=False
        def failing(*args,**kwargs):
            calls.append(True)
            if len(calls)==2:raise RuntimeError('second write')
            return original(*args,**kwargs)
        with patch.object(self.s,'_write',side_effect=failing),self.assertRaises(RuntimeError):self.remove([a['id'],b['id']],['Parent'])
        self.assertEqual(self.s.state(),before);self.assertFalse(self.s.dirty)
    def test_retained_note_validation_and_limit(self):
        raw={'kind':'file','title':'Test','projects':[]}
        for notes in [{1:'note'},{'':'note'},{'x'*81:'note'},{' name':'note'},{'Name':'x'*2001},{'N'+str(i):'' for i in range(1001)}]:
            with self.subTest(notes=str(notes)[:40]),self.assertRaises(ValueError):validate({**raw,'projectNotes':notes})
        notes={'N'+str(i):'' for i in range(1000)};self.assertEqual(len(validate({**raw,'projectNotes':notes})['projectNotes']),1000)
        with self.assertRaises(ValueError):validate({**raw,'projectNotes':notes,'projects':['new']})

class ProjectRemovalHTTP(unittest.TestCase):
    setUp=fixture.Integration.setUp;tearDown=fixture.Integration.tearDown;start=fixture.Integration.start;req=fixture.Integration.req
    def test_endpoint_notes_retained_and_origin(self):
        r=self.req('/api/resources','POST',{'kind':'file','title':'Target','projects':['P'],'projectNotes':{'P':'Use this note'}})['resource']
        self.req('/api/projects/remove','POST',{'ids':[r['id']],'projects':['P']});after=self.req('/api/resources')['resources'][0];self.assertEqual(after['projects'],[]);self.assertEqual(after['projectNotes'],{'P':'Use this note'})
        self.req('/api/projects/remove','POST',{'ids':[r['id']],'projects':['missing']},status=400)
        self.req('/api/projects/remove','POST',{'ids':[r['id']],'projects':['P']},status=403,headers={'Origin':'https://evil.example'})
