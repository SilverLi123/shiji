import sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store,Duplicate
from quick_capture import fallback_title
class QuickCaptureTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name);self.url='https://github.com/openai/codex';self.r=self.store.save({'title':fallback_title(self.url),'url':self.url,'inbox':True})['resource'];self.body={'url':self.r['url'],'updatedAt':self.r['updatedAt']}
 def tearDown(self):self.tmp.cleanup()
 def test_persist_before_enrich_and_no_covers(self):
  self.assertEqual(Store(self.tmp.name).get(self.r['id'])['title'],'openai/codex · GitHub')
  with patch('capture.metadata',return_value={'status':'ok','title':'Codex','description':'Tool','thumbnail':'https://example.com/image.png','favicon':'https://example.com/favicon.ico'}):result=self.store.enrich_capture(self.r['id'],self.body)
  self.assertEqual(result['status'],'completed');r=result['resource'];self.assertEqual(r['title'],'Codex');self.assertEqual(r['description'],'Tool');self.assertEqual(r['thumbnail'],'');self.assertEqual(r['favicon'],'');self.assertEqual(r['attachments'],[]);self.assertFalse(self.store.preview_status()['enabled'])
  with self.store.connect() as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
 def test_inflight_manual_edits_skip_all_metadata_without_locking_requests(self):
  entered=threading.Event();release=threading.Event();result=[]
  def fetch(url):entered.set();release.wait(3);return {'status':'ok','title':'Auto','description':'Auto'}
  with patch('capture.metadata',side_effect=fetch):
   t=threading.Thread(target=lambda:result.append(self.store.enrich_capture(self.r['id'],self.body)));t.start();self.assertTrue(entered.wait(1))
   self.store.edit_resource(self.r['id'],{'changes':{'title':'Mine','notes':'Keep','tags':['New, exact'],'license':'需署名'},'expected':{'title':self.r['title'],'notes':'','tags':[],'license':'待确认'}})
   release.set();t.join(3)
  self.assertEqual(result[0]['status'],'skipped');r=self.store.get(self.r['id']);self.assertEqual(r['title'],'Mine');self.assertEqual(r['tags'],['New, exact']);self.assertEqual(r['license'],'需署名');self.assertEqual(r['notes'],'Keep')
 def test_stale_url_deleted_and_failed_fetch_leave_persisted_data(self):
  with patch('capture.metadata',return_value={'status':'unknown'}):self.assertEqual(self.store.enrich_capture(self.r['id'],self.body)['status'],'unavailable')
  self.assertEqual(self.store.get(self.r['id']),self.r)
  self.store.save({'url':'https://example.com/'},self.r['id'])
  with patch('capture.metadata') as fetch:self.assertEqual(self.store.enrich_capture(self.r['id'],self.body)['status'],'skipped');fetch.assert_not_called()
  with self.assertRaises(Duplicate):self.store.save({'title':'Duplicate','url':'https://example.com/'})
 def test_public_fetch_failure_never_removes_saved_resource(self):
  with patch('capture.metadata',side_effect=OSError('offline')):self.assertEqual(self.store.enrich_capture(self.r['id'],self.body)['status'],'unavailable')
  self.assertEqual(self.store.get(self.r['id']),self.r)
 def test_attachments_during_fetch_are_retained(self):
  def fetch(url):self.store.attachment(self.r['id'],b'\x89PNG\r\n\x1a\nfixture',{'name':'mine.png','cover':True});return {'status':'ok','title':'Auto'}
  with patch('capture.metadata',side_effect=fetch):self.assertEqual(self.store.enrich_capture(self.r['id'],self.body)['status'],'skipped')
  self.assertEqual(self.store.get(self.r['id'])['attachments'][0]['name'],'mine.png')
if __name__=='__main__':unittest.main()
