import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store

class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
  self.r=self.s.save({'title':'One','url':'https://example.com/'})['resource']
 def tearDown(self):self.temp.cleanup()
 def test_trash_undo_membership_and_expiry(self):
  original=self.s.get(self.r['id']);receipt=self.s.batch({'action':'delete','ids':[self.r['id']]})
  self.assertTrue(self.s.get(self.r['id'])['deleted']);self.s.undo(receipt['undoToken']);self.assertEqual(original,self.s.get(self.r['id']))
  with self.assertRaises(ValueError):self.s.undo(receipt['undoToken'])
  receipt=self.s.batch({'action':'delete','ids':[self.r['id']]})
  with patch('recovery.time.monotonic',return_value=time.monotonic()+16):
   with self.assertRaises(ValueError):self.s.undo(receipt['undoToken'])
  self.assertTrue(self.s.get(self.r['id'])['deleted'])
 def test_smart_undo_exact_and_conflict(self):
  smart=self.s.smart({'name':'New, exact','filters':{'tags':['New, exact']}});before=self.s.state()['smartCollections']
  receipt=self.s.delete_smart(smart['id']);self.s.undo(receipt['undoToken']);self.assertEqual(before,self.s.state()['smartCollections'])
  receipt=self.s.delete_smart(smart['id']);self.s.smart({'name':smart['name'],'filters':{}})
  with self.assertRaises(ValueError):self.s.undo(receipt['undoToken'])
  self.assertEqual(1,len(self.s.state()['smartCollections']))
 def test_preflight_cancel_no_changes_and_confirm_single_use(self):
  backup=self.s.create_backup();self.s.remove(self.r['id']);before=self.s.get(self.r['id']);names=set(self.s.backups.iterdir())
  preview=self.s.preflight_backup(backup['name']);self.assertEqual(preview['summary']['active'],1)
  self.assertEqual(before,self.s.get(self.r['id']));self.assertEqual(names,set(self.s.backups.iterdir()))
  with self.assertRaises(ValueError):self.s.confirm_restore({'ticket':preview['ticket']})
  self.s.cancel_restore(preview['ticket']);self.assertEqual(before,self.s.get(self.r['id']))
  self.assertFalse(list(self.s.root.glob('restore-preview-*')))
  with self.assertRaises(ValueError):self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True})
  preview=self.s.preflight_backup(backup['name']);self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True})
  self.assertFalse(self.s.get(self.r['id'])['deleted'])
  with self.assertRaises(ValueError):self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True})
 def test_snapshot_restore_and_safe_paths(self):
  snapshot=self.s.create_snapshot();self.s.remove(self.r['id']);preview=self.s.preflight_backup(snapshot['name']);self.s.confirm_restore({'ticket':preview['ticket'],'confirm':True});self.assertFalse(self.s.get(self.r['id'])['deleted'])
  with self.assertRaises(ValueError):self.s.preflight_backup('../library.sqlite3')
  with self.s.connect() as c:self.assertEqual(3,c.execute('PRAGMA user_version').fetchone()[0])
 def test_bad_archive_expiry_and_quota(self):
  with self.assertRaises(ValueError):self.s.preflight_restore(b'broken')
  self.assertFalse(list(self.s.root.glob('restore-preview-*')))
  zipfile=self.s.backup_file(self.s.create_backup()['name']);a=self.s.preflight_restore(zipfile);b=self.s.preflight_restore(zipfile)
  with self.assertRaises(ValueError):self.s.preflight_restore(zipfile)
  with patch('recovery.time.monotonic',return_value=time.monotonic()+601):
   with self.assertRaises(ValueError):self.s.confirm_restore({'ticket':a['ticket'],'confirm':True})
  self.assertFalse(list(self.s.root.glob('restore-preview-*')))
if __name__=='__main__':unittest.main()
