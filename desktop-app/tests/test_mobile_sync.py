import copy,hashlib,tempfile,unittest,uuid
from pathlib import Path
from storage import Store
from mobile_sync import SyncEngine,RevisionConflict

class MobileSyncTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.store=Store(self.temp.name);self.engine=SyncEngine(self.store)
 def record(self,title='Phone',url='https://example.com/phone'):
  return {'id':str(uuid.uuid4()),'title':title,'url':url,'kind':'website','tags':['New, exact'],'projects':[],'projectNotes':{},'createdAt':'2026-10-07T01:00:00Z','attachments':[],'deleted':False}
 def commit(self,records,revision=None,request=None):
  snapshot=self.engine.snapshot()
  return self.engine.commit({'version':1,'libraryId':snapshot['libraryId'],'expectedRevision':revision or snapshot['revision'],'requestId':request or str(uuid.uuid4()),'resources':records})
 def test_roundtrip_identity_exact_tags_and_trash(self):
  r=self.record();result=self.commit([r]);self.assertEqual(result['resources'][0]['id'],r['id']);self.assertEqual(result['resources'][0]['tags'],['New, exact'])
  r=result['resources'][0];r['deleted']=True;self.commit([r]);self.assertEqual(len(self.store.state(True)['resources']),1)
 def test_stale_revision_never_overwrites_desktop(self):
  r=self.record();s=self.commit([r]);self.store.save({'title':'New desktop'},r['id'])
  with self.assertRaises(RevisionConflict):self.commit([{**s['resources'][0],'title':'Phone edit'}],s['revision'])
  self.assertEqual(self.store.get(r['id'])['title'],'New desktop')
 def test_idempotent_retry_preserves_later_edits(self):
  r=self.record();s=self.engine.snapshot();request=str(uuid.uuid4());body={'version':1,'libraryId':s['libraryId'],'expectedRevision':s['revision'],'requestId':request,'resources':[r]}
  self.engine.commit(body);self.store.save({'notes':'later'},r['id']);self.engine.commit(body)
  self.assertEqual(self.store.get(r['id'])['notes'],'later');self.assertEqual(len(self.store.state()['resources']),1)
  with self.assertRaises(ValueError):self.engine.commit({**body,'resources':[{**r,'title':'other'}]})
 def test_attachment_bytes_and_metadata_are_immutable(self):
  r=self.record();aid=str(uuid.uuid4());raw=b'\xff\xd8\xfffixture';digest=hashlib.sha256(raw).hexdigest()
  self.engine.stage(aid,raw,digest)
  r['attachments']=[{'id':aid,'resourceId':r['id'],'name':'cover.jpg','mime':'image/jpeg','size':len(raw),'sha256':digest,'createdAt':r['createdAt'],'license':'待确认','colors':[]}];r['coverId']=aid
  self.commit([r]);self.assertEqual(self.engine.file(aid)[0],raw)
  with self.assertRaises(ValueError):self.engine.stage(aid,b'changed',hashlib.sha256(b'changed').hexdigest())
  with self.assertRaises(ValueError):self.engine.stage(str(uuid.uuid4()),raw,'0'*64)
 def test_missing_attachment_and_batch_error_roll_back(self):
  r=self.record();bad=self.record('bad','https://example.com/bad');bad['title']=''
  before=self.engine.snapshot()
  with self.assertRaises(ValueError):self.commit([r,bad])
  self.assertEqual(self.engine.snapshot()['revision'],before['revision'])
  r['coverId']=str(uuid.uuid4())
  with self.assertRaises(ValueError):self.commit([r])
  self.assertEqual(self.store.state()['resources'],[])
 def test_url_collision_and_wrong_library(self):
  a=self.record();self.commit([a]);b=self.record()
  with self.assertRaises(ValueError):self.commit([b])
  s=self.engine.snapshot()
  with self.assertRaises(ValueError):self.engine.commit({'version':1,'libraryId':'different','expectedRevision':s['revision'],'requestId':str(uuid.uuid4()),'resources':[]})
 def test_snapshot_includes_desktop_and_deleted_records(self):
  a=self.store.save({'title':'Desktop','url':'https://example.com/desktop'})['resource'];self.store.remove(a['id'])
  s=self.engine.snapshot();self.assertTrue(s['resources'][0]['deleted']);self.assertEqual(s['libraryId'],SyncEngine(self.store).snapshot()['libraryId'])

 def test_existing_attachments_do_not_count_as_transfer(self):
  from unittest.mock import patch
  rows=[]
  for i in range(2):
   r=self.record(str(i),'https://example.com/'+str(i));aid=str(uuid.uuid4());raw=b'\xff\xd8\xfffixture';sha=hashlib.sha256(raw).hexdigest();self.engine.stage(aid,raw,sha)
   r['attachments']=[{'id':aid,'resourceId':r['id'],'name':'a.jpg','mime':'image/jpeg','size':len(raw),'sha256':sha,'license':'待确认','colors':[]}];rows.append(r)
  self.commit(rows)
  for r in rows:r['notes']='Changed notes only'
  with patch('mobile_sync.MAX_TOTAL',1):self.commit(rows)
  self.assertTrue(all(r['notes']=='Changed notes only' for r in self.engine.snapshot()['resources']))
 def test_expired_staging_is_reclaimed(self):
  import os,time
  old=self.engine.staging/str(uuid.uuid4());old.write_bytes(b'expired');os.utime(old,(time.time()-90000,time.time()-90000))
  raw=b'new';self.engine.stage(str(uuid.uuid4()),raw,hashlib.sha256(raw).hexdigest());self.assertFalse(old.exists())
 def test_empty_collections_are_preserved_in_snapshot(self):
  with self.store.lock,self.store.connect() as c:c.execute("INSERT INTO collections(name) VALUES('Empty project')")
  self.assertIn('Empty project',self.engine.snapshot()['collections'])
