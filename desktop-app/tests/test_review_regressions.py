import sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store
PNG=b'\x89PNG\r\n\x1a\nfixture'
class FinalReviewRegressions(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name);self.r=self.s.save({'title':'First','url':'https://example.com/'})['resource']
 def tearDown(self):self.s.stop_preview_worker();self.temp.cleanup()
 def test_same_size_object_corruption_is_repaired_without_recopying_intact(self):
  a=self.s.attachment(self.r['id'],PNG,{'name':'x.png'})['attachment'];self.s.create_snapshot();obj=self.s.backups/'objects'/a['sha256'];obj.chmod(0o644);obj.write_bytes(PNG[:-1]+b'X');self.s.save({'notes':'changed'},self.r['id']);snapshot=self.s.create_snapshot();self.assertEqual(obj.read_bytes(),PNG);ticket=self.s.preflight_backup(snapshot['name']);self.s.cancel_restore(ticket['ticket'])
 def test_abandoned_staging_expires_via_background_and_startup(self):
  self.s.attachment(self.r['id'],PNG,{'name':'x.png'});blob=self.s.backup_bytes();preview=self.s.preflight_restore(blob)
  with patch('recovery.time.monotonic',return_value=time.monotonic()+601),patch('recovery.time.time',return_value=time.time()+601):
   self.s.start_preview_worker();deadline=time.perf_counter()+3
   while list(self.s.root.glob('restore-preview-*')) and time.perf_counter()<deadline:time.sleep(.05)
   self.s.stop_preview_worker()
  self.assertFalse(list(self.s.root.glob('restore-preview-*')))
  self.s.preflight_restore(blob)
  with patch('recovery.time.time',return_value=time.time()+601):Store(self.temp.name)
  self.assertFalse(list(self.s.root.glob('restore-preview-*')))
 def test_restore_invalidates_old_trash_undo_after_commit_only(self):
  self.s.remove(self.r['id']);blob=self.s.backup_bytes();self.s.remove(self.r['id'],True);self.s.save({'title':'New'},self.r['id']);receipt=self.s.batch({'action':'delete','ids':[self.r['id']]});preview=self.s.preflight_restore(blob);self.s.cancel_restore(preview['ticket']);self.s.undo(receipt['undoToken'])
  receipt=self.s.batch({'action':'delete','ids':[self.r['id']]});preview=self.s.preflight_restore(blob);self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True})
  with self.assertRaises(ValueError):self.s.undo(receipt['undoToken'])
  self.assertTrue(self.s.get(self.r['id'])['deleted']);self.assertEqual(self.s.get(self.r['id'])['title'],'First')
 def test_saved_remote_thumbnail_is_a_chosen_preview(self):
  self.s.save({'thumbnail':'https://example.com/chosen.png'},self.r['id']);self.s.configure_previews({'enabled':True})
  with patch('capture.website_preview',return_value=(PNG,'https://example.com/other.png','og:image')) as fetch:self.assertFalse(self.s.preview_step());fetch.assert_not_called()
  self.assertEqual(self.s.get(self.r['id'])['coverId'],'');self.assertEqual(self.s.preview_status()['pending'],0)

 def test_active_preflight_is_not_reaped_and_failed_restore_keeps_undo(self):
  import threading
  blob=self.s.backup_bytes();original=self.s._validate_archive;entered=threading.Event();release=threading.Event();result=[]
  def validate(*args):entered.set();release.wait(2);return original(*args)
  with patch.object(self.s,'_validate_archive',side_effect=validate):
   worker=threading.Thread(target=lambda:result.append(self.s.preflight_restore(blob)));worker.start();self.assertTrue(entered.wait(1))
   with patch('recovery.time.monotonic',return_value=time.monotonic()+601),patch('recovery.time.time',return_value=time.time()+601):self.s.cleanup_restore_staging()
   self.assertTrue(list(self.s.root.glob('restore-preview-*')));release.set();worker.join(2)
  self.s.cancel_restore(result[0]['ticket']);receipt=self.s.batch({'action':'delete','ids':[self.r['id']]});preview=self.s.preflight_restore(blob)
  with patch.object(self.s,'_apply_archive',side_effect=ValueError('disk failure')):
   with self.assertRaises(ValueError):self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True})
  self.s.undo(receipt['undoToken']);self.assertFalse(self.s.get(self.r['id'])['deleted'])
