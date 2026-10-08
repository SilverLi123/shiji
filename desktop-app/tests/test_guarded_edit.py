import json,sqlite3,tempfile,threading,unittest,sys
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store

class GuardedEdit(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def resource(self):return self.store.save({'kind':'file','title':'Original','notes':'Note A','projects':['__proto__','P'],'projectNotes':{'__proto__':'Proto A','History':'History A'},'tags':['tag,a'],'author':'Keep','license':'需署名'})['resource']
 def edit(self,r,changes,expected):return self.store.edit_resource(r['id'],{'changes':changes,'expected':expected})
 def test_different_fields_merge_and_idempotence(self):
  r=self.resource();self.store.save({'notes':'Other note','favorite':True,'tags':['Latest']},r['id']);latest=self.store.get(r['id']);x=self.edit(r,{'title':'My title'},{'title':r['title']});self.assertTrue(x['changed']);self.assertEqual(x['resource']['title'],'My title')
  for k in latest:
   if k not in ('title','updatedAt'):self.assertEqual(x['resource'][k],latest[k],k)
  self.store.dirty=False;before=self.store.state();self.assertFalse(self.edit(r,{'title':' My title '},{'title':'Original'})['changed']);self.assertFalse(self.edit(r,{}, {})['changed']);self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
 def test_same_field_conflict_whole_patch_and_explicit_retry(self):
  r=self.resource();self.store.save({'notes':'Other note'},r['id']);before=self.store.state();self.store.dirty=False
  with self.assertRaises(ValueError) as error:self.edit(r,{'notes':'Draft','author':'New'},{'notes':'Note A','author':'Keep'})
  e=error.exception;self.assertEqual(e.resource['notes'],'Other note');self.assertEqual(e.conflicts,[{'field':'notes','current':'Other note','value':'Draft'}]);self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  x=self.edit(r,{'notes':'Draft','author':'New'},{'notes':'Other note','author':'Keep'});self.assertEqual(x['resource']['author'],'New')
 def test_per_key_project_notes_preserve_exact_history_membership(self):
  r=self.resource();self.store.update_note(r['id'],{'kind':'project','project':'History','expected':'History A','value':'Other history'})
  x=self.edit(r,{'projectNotes':{'__proto__':'Proto B','New\x00key':''}},{'projectNotes':{'__proto__':'Proto A','New\x00key':None}})['resource'];self.assertEqual(x['projectNotes']['History'],'Other history');self.assertEqual(x['projectNotes']['__proto__'],'Proto B');self.assertEqual(x['projects'],r['projects'])
  with self.assertRaises(ValueError) as e:self.edit(r,{'projectNotes':{'__proto__':'Draft'}},{'projectNotes':{'__proto__':'Proto A'}})
  self.assertEqual(e.exception.conflicts[0]['key'],'__proto__')
  self.store.update_collection({'original':'P','name':'Renamed'})
  with self.assertRaises(ValueError) as e:self.edit(r,{'projects':[]},{'projects':r['projects']})
  self.assertEqual(e.exception.conflicts[0]['field'],'projects');self.assertNotIn('P',self.store.state()['collections'])
 def test_historical_kind_and_url_are_validated_independently(self):
  r=self.store.save({'title':'Website','kind':'website','url':'https://example.test/'})['resource'];self.store.save({'kind':'file','url':''},r['id']);before=self.store.state();self.store.dirty=False
  with self.assertRaises(ValueError) as caught:self.edit(r,{'kind':'prompt'},{'kind':'website'})
  self.assertTrue(hasattr(caught.exception,'conflicts'))
  self.assertEqual(caught.exception.conflicts,[{'field':'kind','current':'file','value':'prompt'}]);self.assertEqual(self.store.state(),before)
  self.assertFalse(self.edit(r,{'kind':'file'},{'kind':'website'})['changed']);self.assertFalse(self.store.dirty)
  self.store.save({'kind':'prompt'},r['id'])
  with self.assertRaises(ValueError) as caught:self.edit(r,{'kind':'website'},{'kind':'file'})
  self.assertEqual(caught.exception.conflicts,[{'field':'kind','current':'prompt','value':'website'}])
  with self.assertRaises(ValueError) as caught:self.edit(r,{'kind':'website'},{'kind':'prompt'})
  self.assertFalse(hasattr(caught.exception,'conflicts'),'a matching baseline still requires a valid website URL')
  current=self.store.state()['resources'][0]
  self.assertEqual(current['kind'],'prompt')
 def test_historical_project_baseline_at_retained_note_limit(self):
  notes={'P':'Project note',**{f'History {i}':'note' for i in range(999)}}
  r=self.store.save({'kind':'file','title':'Many notes','projects':['P'],'projectNotes':notes})['resource'];self.store.update_collection({'original':'P','name':'R'});before=self.store.state();self.store.dirty=False
  with self.assertRaises(ValueError) as caught:self.edit(r,{'projects':[]},{'projects':['P']})
  self.assertTrue(hasattr(caught.exception,'conflicts'));self.assertEqual(caught.exception.conflicts,[{'field':'projects','current':['R'],'value':[]}]);self.assertEqual(self.store.state(),before)
  self.assertFalse(self.edit(r,{'projects':['R']},{'projects':['P']})['changed']);self.assertFalse(self.store.dirty)
 def test_automatic_cover_cache_preserves_newer_cover_and_thumbnail(self):
  r=self.resource();image='https://example.test/image.png';self.store.save({'thumbnail':image},r['id'])
  a=self.store.attachment(r['id'],fixture.PNG,{'name':'Chosen cover','cover':True,'colors':['#123456']})['attachment'];self.store.dirty=False;before=self.store.state()
  result=self.store.cache_cover(r['id'],fixture.PNG,'https://example.test/final.png',image)
  self.assertTrue(result['skipped']);self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  self.assertEqual(self.store.get(r['id'])['coverId'],a['id'])
  self.store.save({'coverId':'','thumbnail':'https://example.test/new.png'},r['id']);before=self.store.state()
  self.assertTrue(self.store.cache_cover(r['id'],fixture.PNG,'https://example.test/final.png',image)['skipped']);self.assertEqual(self.store.state(),before)
  result=self.store.cache_cover(r['id'],fixture.PNG,'https://example.test/final.png','https://example.test/new.png');self.assertEqual(self.store.get(r['id'])['coverId'],result['attachment']['id']);self.assertEqual(result['attachment']['sourceUrl'],'https://example.test/final.png')
 def test_cover_uses_latest_attachment_palette_and_preserves_everything_else(self):
  r=self.resource();a=self.store.attachment(r['id'],fixture.PNG,{'name':'cover.png','colors':['#123456']})['attachment'];self.store.update_attachment(a['id'],{'colors':['#abcdef'],'author':'Image author'});latest=self.store.save({'notes':'Latest'},r['id'])['resource'];b=self.edit(r,{'coverId':a['id']},{'coverId':''})['resource'];self.assertEqual(b['colors'],['#abcdef']);self.assertEqual(b['notes'],'Latest');self.assertEqual((self.store.files/a['id']).read_bytes(),fixture.PNG)
  self.store.dirty=False;before=self.store.state();self.assertFalse(self.edit(r,{'coverId':a['id']},{'coverId':''})['changed']);self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  other=self.resource();foreign=self.store.attachment(other['id'],fixture.PNG,{'name':'foreign'})['attachment']
  with self.assertRaises(ValueError):self.edit(r,{'coverId':foreign['id']},{'coverId':a['id']})
 def test_limits_strict_body_immutable_trash_and_atomic_rollback(self):
  r=self.resource();before=self.store.state();self.store.dirty=False
  bad=[None,{}, {'changes':{},'expected':{},'extra':True}, {'changes':{'title':'X'},'expected':{}}, {'changes':{'id':'new'},'expected':{'id':r['id']}}, {'changes':{'favorite':1},'expected':{'favorite':False}}, {'changes':{'projectNotes':{'P':'A'}},'expected':{'projectNotes':{}}}, {'changes':{'projectNotes':{'P':'A'}},'expected':{'projectNotes':{'P':2}}}]
  for x in bad:
   with self.assertRaises(ValueError):self.store.edit_resource(r['id'],x)
   self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  with self.assertRaises(ValueError):self.edit(r,{'notes':'💡'*10001},{'notes':r['notes']})
  self.assertEqual(self.edit(r,{'notes':'💡'*10000},{'notes':r['notes']})['resource']['notes'],'💡'*10000)
  original=self.store._projects;before=self.store.state();self.store.dirty=False
  def fail(c,item):original(c,item);raise sqlite3.OperationalError('rollback')
  with patch.object(self.store,'_projects',side_effect=fail):
   with self.assertRaises(sqlite3.OperationalError):self.edit(r,{'projects':['New']},{'projects':r['projects']})
  self.assertEqual(self.store.state(),before);self.assertFalse(self.store.dirty)
  self.store.remove(r['id'])
  with self.assertRaises(ValueError):self.edit(r,{}, {})
 def test_two_writers_conflict_not_last_write_wins(self):
  r=self.resource();barrier=threading.Barrier(3);results=[]
  def writer(value):
   barrier.wait()
   try:self.edit(r,{'notes':value},{'notes':'Note A'});results.append('saved')
   except ValueError:results.append('conflict')
  ts=[threading.Thread(target=writer,args=(v,)) for v in ['One','Two']]
  for t in ts:t.start()
  barrier.wait()
  for t in ts:t.join()
  self.assertCountEqual(results,['saved','conflict'])
 def test_json_zip_and_restart_keep_schema_ids_and_bytes(self):
  r=self.resource();a=self.store.attachment(r['id'],fixture.PNG,{'name':'Asset','license':'需署名'})['attachment'];result=self.edit(r,{'notes':'New'},{'notes':'Note A'})['resource'];self.assertEqual(Store(self.temp.name).get(r['id']),result)
  exported=self.store.export();self.assertEqual(exported['schemaVersion'],3)
  blob=self.store.backup_bytes();other=tempfile.TemporaryDirectory()
  try:
   second=Store(other.name);second.restore_zip(blob);self.assertEqual({k:v for k,v in second.get(r['id']).items() if k!='updatedAt'},{k:v for k,v in result.items() if k!='updatedAt'});self.assertEqual((second.files/a['id']).read_bytes(),fixture.PNG)
  finally:other.cleanup()

class GuardedEditHTTP(unittest.TestCase):
 setUp=fixture.Integration.setUp;start=fixture.Integration.start;tearDown=fixture.Integration.tearDown;req=fixture.Integration.req
 def test_edit_route_atomic_conflict_origin_and_compatibility(self):
  r=self.req('/api/resources','POST',{'kind':'file','title':'Target','notes':'A'})['resource'];url='/api/resources/'+r['id'];body={'changes':{'notes':'B'},'expected':{'notes':'A'}}
  self.assertTrue(self.req(url+'/edit','POST',body)['changed']);e=self.req(url+'/edit','POST',{'changes':{'notes':'C'},'expected':{'notes':'A'}},status=409);self.assertEqual(e['resource']['notes'],'B');self.assertEqual(e['conflicts'][0]['field'],'notes')
  self.req(url+'/edit','POST',body,status=403,headers={'Origin':'https://evil.example'});self.req(url+'/edit','PUT',body,status=404)
  self.assertEqual(self.req(url,'PUT',{'title':'Legacy'})['resource']['notes'],'B')

class AutomaticCoverHTTP(unittest.TestCase):
 def test_remote_route_preserves_changes_before_and_during_fetch(self):
  import server
  from http.server import ThreadingHTTPServer
  from urllib.request import Request,urlopen
  with tempfile.TemporaryDirectory() as directory:
   store=Store(directory);previous=server.STORE;server.STORE=store
   http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
   try:
    old='https://example.test/old.png';new='https://example.test/new.png'
    r=store.save({'title':'Remote cache','kind':'file','thumbnail':old})['resource'];chosen=[]
    def fetch(*args,**kwargs):
     chosen.append(store.attachment(r['id'],fixture.PNG,{'name':'User cover','cover':True,'colors':['#123456']})['attachment'])
     return 200,{},fixture.PNG,old
    def request():
     body=json.dumps({'id':r['id'],'url':old}).encode()
     with urlopen(Request(f'http://127.0.0.1:{http.server_port}/api/remote-cover',data=body,headers={'Content-Type':'application/json'})) as response:return json.load(response)
    with patch.object(server,'public_fetch',side_effect=fetch):self.assertTrue(request()['skipped'])
    latest=store.get(r['id']);self.assertEqual(latest['coverId'],chosen[0]['id']);self.assertEqual(len(latest['attachments']),1)
    store.save({'coverId':'','thumbnail':new},r['id']);before=store.state()
    with patch.object(server,'public_fetch',return_value=(200,{},fixture.PNG,old)):self.assertTrue(request()['skipped'])
    self.assertEqual(store.state(),before)
   finally:
    http.shutdown();worker.join();http.server_close();server.STORE=previous
