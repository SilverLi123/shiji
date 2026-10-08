import hashlib,json,sqlite3,tempfile,threading,unittest,sys,uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store,dump
import backups

class BackupLifecycle(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.r=self.store.save({'kind':'file','title':'Target'})['resource'];self.a=self.store.attachment(self.r['id'],fixture.PNG,{'name':'image.png'})['attachment']
 def tearDown(self):
  if hasattr(self.store,'stop_auto_backup'):self.store.stop_auto_backup()
  self.temp.cleanup()
 def test_incremental_objects_and_snapshot_roundtrip(self):
  with patch.object(backups,'copy_checked',wraps=backups.copy_checked) as copied:
   first=self.store.create_snapshot();count=copied.call_count
   self.store.save({'notes':'New note'},self.r['id']);second=self.store.create_snapshot()
   self.assertGreater(count,0);self.assertEqual(copied.call_count,count)
  objects=list((self.store.backups/'objects').iterdir());self.assertEqual(len(objects),1);self.assertEqual(objects[0].read_bytes(),fixture.PNG)
  with sqlite3.connect(self.store.backups/second['name']/'library.sqlite3') as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3);self.assertEqual(json.loads(c.execute('SELECT payload FROM resources').fetchone()[0])['notes'],'New note')
  self.assertFalse(list(self.store.backups.glob('shiji-*.zip')))
 def test_tiered_retention_cleans_unreferenced_objects(self):
  at=datetime(2026,10,6,12,tzinfo=timezone.utc)
  for i in range(0,24*40,3):self.store.create_snapshot(at=at-timedelta(hours=i))
  result=self.store.prune_backups(at=at);rows=self.store.backup_list()['snapshots'];self.assertLessEqual(len(rows),24+7+4)
  self.assertTrue(result['removed']);self.assertFalse(any(at-datetime.fromisoformat(r['createdAt'])>timedelta(weeks=4) for r in rows))
  orphan=self.store.backups/'objects'/('0'*64);orphan.write_bytes(b'orphan');self.store.prune_backups(at=at);self.assertFalse(orphan.exists());self.assertTrue((self.store.backups/'objects'/self.a['sha256']).exists())
 def test_zip_compression_does_not_hold_store_lock_or_clear_new_writes(self):
  started=threading.Event();finish=threading.Event();original=backups.copy_checked;errors=[]
  def slow(*a,**kw):started.set();finish.wait(3);return original(*a,**kw)
  def make():
   try:self.store.create_backup()
   except Exception as e:errors.append(e)
  with patch.object(backups,'copy_checked',side_effect=slow):
   worker=threading.Thread(target=make);worker.start();self.assertTrue(started.wait(3));responsive=threading.Event()
   writer=threading.Thread(target=lambda:(self.store.save({'notes':'Concurrent'},self.r['id']),responsive.set()));writer.start()
   try:self.assertTrue(responsive.wait(.5),'ZIP compression blocks writes')
   finally:finish.set();worker.join();writer.join()
  self.assertFalse(errors);self.assertTrue(self.store.dirty)
 def test_256mib_incremental_copy_allows_requests(self):
  block=b'X'*1024*1024
  for i in range(4):
   block=bytes([65+i])*1024*1024;aid=str(uuid.uuid4());file=self.store.files/aid;digest=hashlib.sha256()
   with file.open('wb') as out:
    for _ in range(64):out.write(block);digest.update(block)
   item={**self.a,'id':aid,'name':f'big-{i}.bin','mime':'application/octet-stream','size':64*1024*1024,'sha256':digest.hexdigest()}
   with self.store.connect() as c:c.execute('INSERT INTO attachments VALUES(?,?,?,0)',(aid,self.r['id'],dump(item)))
  started=threading.Event();finish=threading.Event();original=backups.copy_checked;errors=[]
  def slow(*a,**kw):started.set();finish.wait(3);return original(*a,**kw)
  def make():
   try:self.store.create_snapshot()
   except Exception as e:errors.append(e)
  with patch.object(backups,'copy_checked',side_effect=slow):
   worker=threading.Thread(target=make);worker.start();self.assertTrue(started.wait(3));done=threading.Event()
   request=threading.Thread(target=lambda:(self.store.get(self.r['id']),self.store.backup_list(),done.set()));request.start()
   try:self.assertTrue(done.wait(.5),'attachment copying blocks requests')
   finally:finish.set();worker.join();request.join()
  self.assertFalse(errors);self.assertEqual(self.store.get(self.r['id'])['title'],'Target')
 def test_failure_is_unpublished_and_startup_is_asynchronous(self):
  self.store.files.joinpath(self.a['id']).unlink()
  with self.assertRaises(ValueError):self.store.create_snapshot()
  self.assertFalse(self.store.backup_list()['snapshots']);self.assertIn('缺失',self.store.backup_list()['warning'])
  entered=threading.Event();release=threading.Event()
  def slow():entered.set();release.wait(2)
  with patch.object(self.store,'create_snapshot',side_effect=slow),patch.object(self.store,'create_backup') as zipped:
   self.store.start_auto_backup();self.assertTrue(entered.wait(1));self.assertFalse(zipped.called);release.set();self.store.stop_auto_backup()
