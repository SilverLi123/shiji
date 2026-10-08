import json,sqlite3,sys,tempfile,unittest
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store,NoteConflict

class QuickNotes(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def resource(self):return self.store.save({'kind':'file','title':'Keep','notes':'Original','projects':['__proto__','Current'],'projectNotes':{'__proto__':'Project original','History':'Earlier'},'tags':['Keep'],'author':'Author','sourceUrl':'https://example.com/source','license':'待确认'})['resource']
 def update(self,r,kind='notes',project='',expected='Original',value='Edited'):return self.store.update_note(r['id'],{'kind':kind,'project':project,'expected':expected,'value':value})
 def test_targeted_write_preserves_latest_other_fields_and_bytes(self):
  r=self.resource();a=self.store.attachment(r['id'],fixture.PNG,{'name':'Asset.png','author':'Asset author','cover':True})['attachment']
  latest=self.store.save({'title':'Concurrent title','favorite':True,'tags':['Concurrent'],'description':'Changed'},r['id'])['resource'];before=self.store.state();trash=self.store.state(True)
  result=self.update(r);after=result['resource'];self.assertTrue(result['changed']);self.assertEqual(after['notes'],'Edited')
  for key in latest:
   if key not in ('notes','updatedAt'):self.assertEqual(after[key],latest[key],key)
  self.assertEqual(self.store.state()['collectionMeta'],before['collectionMeta']);self.assertEqual(self.store.state(True)['resources'],trash['resources']);self.assertEqual((self.store.files/a['id']).read_bytes(),fixture.PNG)
 def test_conflict_and_idempotent_retry(self):
  r=self.resource();self.update(r,value='Other page');before=self.store.state();self.store.dirty=False
  with self.assertRaises(NoteConflict) as error:self.update(r,value='My draft')
  self.assertEqual(error.exception.current,'Other page');self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  self.assertFalse(self.update(r,value='Other page')['changed']);self.assertEqual(self.store.state(),before)
  self.assertTrue(self.update(r,expected='Other page',value='My draft')['changed'])
 def test_project_keys_clear_and_history_do_not_change_memberships(self):
  r=self.resource();before=self.store.get(r['id'])
  for key,expected in [('__proto__','Project original'),('History','Earlier'),('Current','')]:
   self.update(r,'project',key,expected,'  Specific note\nNext  ')
   after=self.store.get(r['id']);self.assertEqual(after['projectNotes'][key],'Specific note\nNext');self.assertEqual(after['notes'],'Original');self.assertEqual(after['projects'],before['projects'])
  self.update(r,'project','__proto__','Specific note\nNext','');self.assertEqual(self.store.get(r['id'])['projectNotes']['__proto__'],'')
  with self.store.connect() as c:self.assertEqual(c.execute('SELECT note FROM resource_projects WHERE resource_id=? AND name=?',(r['id'],'__proto__')).fetchone()[0],'')
 def test_special_key_matrix_and_unicode_limits(self):
  keys=['__proto__','constructor','toString','HTML <"&>','Exact\x00name','中文💡']
  r=self.resource();r=self.store.save({'projectNotes':{k:'A' for k in keys}},r['id'])['resource']
  for k in keys:self.update(r,'project',k,'A','💡'*2000);self.assertEqual(self.store.get(r['id'])['projectNotes'][k],'💡'*2000)
  self.update(r,value='💡'*10000)
  with self.assertRaises(ValueError):self.update(r,expected='💡'*10000,value='💡'*10001)
 def test_archived_and_removed_project_name_rules(self):
  r=self.resource();self.store.update_collection({'original':'__proto__','archived':True});self.update(r,'project','__proto__','Project original','Archived note')
  self.store.update_collection({'original':'Current','name':'Renamed'});before=self.store.state()
  with self.assertRaises(ValueError):self.update(r,'project','Current','','Stale')
  self.assertEqual(self.store.state(),before)
 def test_validation_noop_trash_missing_and_rollback(self):
  r=self.resource();body={'kind':'notes','project':'','expected':'Original','value':'Edited'};before=self.store.state();self.store.dirty=False
  for bad in [None,[],{},dict(body,extra=True),dict(body,kind='bad'),dict(body,project='P'),dict(body,value=1),dict(body,expected=None),dict(body,kind='project',project='Unknown'),dict(body,value='💡'*10001)]:
   with self.subTest(body=str(bad)[:80]),self.assertRaises((ValueError,TypeError)):self.store.update_note(r['id'],bad)
   self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  self.assertFalse(self.update(r,value='  Original  ')['changed']);self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  with patch.object(self.store,'_get',side_effect=[r,sqlite3.OperationalError('after write')]),self.assertRaises(sqlite3.Error):self.update(r)
  self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  self.store.remove(r['id']);before=self.store.state(True)
  with self.assertRaises(ValueError):self.update(r)
  self.assertEqual(self.store.state(True),before)
  with self.assertRaises(ValueError):self.store.update_note('missing',body)
 def test_json_zip_and_restart_preserve_quick_notes(self):
  r=self.resource();self.update(r,value='Saved');self.update(r,'project','History','Earlier','Kept history')
  full=self.store.get(r['id']);backup=self.store.backup_bytes()
  with tempfile.TemporaryDirectory() as d:
   other=Store(d);other.restore_zip(backup);self.assertEqual(other.get(r['id'])['notes'],'Saved');self.assertEqual(other.get(r['id'])['projectNotes'],full['projectNotes'])
  with tempfile.TemporaryDirectory() as d:
   other=Store(d);other.import_json(self.store.export());copy=other.state()['resources'][0];self.assertEqual(copy['notes'],'Saved');self.assertEqual(copy['projectNotes'],full['projectNotes'])
  self.assertEqual(Store(self.temp.name).get(r['id']),full)

class QuickNotesHTTP(unittest.TestCase):
 setUp=fixture.Integration.setUp;start=fixture.Integration.start;tearDown=fixture.Integration.tearDown;req=fixture.Integration.req
 def test_target_read_write_conflict_origin_and_wrong_routes(self):
  r=self.req('/api/resources','POST',{'kind':'file','title':'Target','notes':'Original','license':'待确认'})['resource'];url='/api/resources/'+r['id'];body={'kind':'notes','project':'','expected':'Original','value':'New'}
  self.assertEqual(self.req(url)['resource'],r)
  self.assertTrue(self.req(url+'/note','POST',body)['changed'])
  e=self.req(url+'/note','POST',dict(body,value='Draft'),status=409);self.assertEqual(e['current'],'New');self.assertEqual(e['resource']['notes'],'New');self.assertEqual(e['resource']['id'],r['id'])
  self.req(url+'/note','POST',dict(body,expected='New',value='Wrong origin'),status=403,headers={'Origin':'https://evil.example'})
  self.req(url+'/note','PUT',body,status=404)
  self.req(url+'/note','POST',dict(body,value='x'*10001),status=400)
  self.req(url,'DELETE');self.req(url+'/note','POST',dict(body,expected='New'),status=400)
