import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store
import capture
PNG=__import__('base64').b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGP4DwABAQEAsTj2FAAAAABJRU5ErkJggg==')
class PreviewTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name);self.r=self.s.save({'title':'Example','url':'https://example.com/'})['resource']
 def tearDown(self):self.s.stop_preview_worker();self.temp.cleanup()
 def test_default_off_rate_limit_and_new_resources(self):
  with patch('capture.website_preview',return_value=(PNG,self.r['url'],'og:image')) as fetch:
   self.assertFalse(self.s.preview_step());fetch.assert_not_called();self.s.configure_previews({'enabled':True});self.assertTrue(self.s.preview_step());self.assertTrue(self.s.get(self.r['id'])['coverId'])
   other=self.s.save({'title':'Another','url':'https://example.org/'})['resource'];self.assertFalse(self.s.preview_step());self.assertEqual(fetch.call_count,1)
   with patch('preview_jobs.time.monotonic',return_value=time.monotonic()+31):self.assertTrue(self.s.preview_step())
   self.assertTrue(self.s.get(other['id'])['coverId']);self.assertEqual(self.s.preview_status()['completed'],2)
   with self.assertRaises(ValueError):self.s.configure_previews({'interval':1})
 def test_pause_discards_inflight_and_resume(self):
  self.s.configure_previews({'enabled':True});entered=threading.Event();release=threading.Event()
  def fetch(url):entered.set();release.wait(2);return PNG,url,'og:image'
  with patch('capture.website_preview',side_effect=fetch):
   job=threading.Thread(target=self.s.preview_step);job.start();self.assertTrue(entered.wait(1));self.s.configure_previews({'paused':True});release.set();job.join(2)
  self.assertEqual(self.s.get(self.r['id'])['coverId'],'');self.assertEqual(self.s.get(self.r['id'])['attachments'],[])
  self.s.configure_previews({'paused':False})
  with patch('preview_jobs.time.monotonic',return_value=time.monotonic()+31),patch('capture.website_preview',return_value=(PNG,self.r['url'],'og:image')):self.assertTrue(self.s.preview_step())
 def test_concurrent_manual_cover_and_url_change_preserved(self):
  self.s.configure_previews({'enabled':True})
  def manual(url):self.s.attachment(self.r['id'],PNG,{'name':'mine.png','cover':True});return PNG,url,'Chrome 截图'
  with patch('capture.website_preview',side_effect=manual):self.assertFalse(self.s.preview_step())
  self.assertEqual([a['name'] for a in self.s.get(self.r['id'])['attachments']],['mine.png'])
  other=self.s.save({'title':'Another','url':'https://example.org/'})['resource'];self.s._preview_next=0
  def change(url):self.s.save({'url':'https://example.net/'},other['id']);return PNG,url,'og:image'
  with patch('capture.website_preview',side_effect=change):self.assertFalse(self.s.preview_step())
  self.assertFalse(self.s.get(other['id'])['attachments'])
 def test_failure_preserves_resource_and_can_retry(self):
  before=self.s.get(self.r['id']);self.s.configure_previews({'enabled':True})
  with patch('capture.website_preview',side_effect=ValueError('Blocked')) as fetch:
   self.assertFalse(self.s.preview_step());self.s._preview_next=0;self.assertFalse(self.s.preview_step());self.assertEqual(fetch.call_count,1)
  self.assertEqual(before,self.s.get(self.r['id']));self.assertEqual(self.s.preview_status()['failed'],1);self.s.configure_previews({'retry':True});self.assertEqual(self.s.preview_status()['pending'],1)
 def test_og_image_then_chrome_fallback_and_private_rejection(self):
  html=b'<meta property="og:image" content="/cover.png">'
  with patch('capture.bounded_resolve'),patch('capture.public_fetch',side_effect=[(200,{'content-type':'text/html'},html,self.r['url']),(200,{},PNG,'https://example.com/cover.png')]),patch('capture.chrome_screenshot') as chrome:
   self.assertEqual(capture.website_preview(self.r['url'])[2],'og:image');chrome.assert_not_called()
  with patch('capture.bounded_resolve'),patch('capture.public_fetch',side_effect=OSError()),patch('capture.chrome_screenshot',return_value=(PNG,self.r['url'])):
   self.assertEqual(capture.website_preview(self.r['url'])[2],'Chrome 截图')
  with patch('capture.chrome_screenshot') as chrome:
   with self.assertRaises(ValueError):capture.website_preview('http://127.0.0.1/')
   chrome.assert_not_called()
 def test_configuration_persists_without_schema_change(self):
  self.s.configure_previews({'enabled':True,'paused':True,'interval':60});other=Store(self.temp.name);self.assertTrue(other.preview_status()['paused']);self.assertEqual(other.preview_status()['interval'],60)
  with other.connect() as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
if __name__=='__main__':unittest.main()

class ChromeProxyTests(unittest.TestCase):
 def test_isolated_chrome_proxy_blocks_private_and_redirects(self):
  import http.client
  from urllib.parse import urlsplit
  real_resolve=capture.resolve_public;calls=[];arguments=[]
  def resolve(url,timeout):
   if 'example.com' in url:return url,'example.com',443,'93.184.216.34'
   return real_resolve(url)
  def request(target,*args):
   calls.append(target)
   if target[0].endswith('/redirect'):return 302,{'location':'http://127.0.0.1/'},b''
   return 200,{'content-type':'text/html'},b'A'*1500
  class FakeChrome:
   pid=987654321;returncode=0
   def __init__(self,args,**kwargs):arguments.extend(args);self.args=args;self.first=True
   def wait(self,timeout=None):
    if not self.first:return 0
    self.first=False;proxy=urlsplit(next(a.split('=',1)[1] for a in self.args if a.startswith('--proxy-server=')))
    for method,path,status in [('CONNECT','localhost:443',403),('GET','http://127.0.0.1/',403),('GET','https://example.com/redirect',403),('GET','https://example.com/',200)]:
     c=http.client.HTTPConnection(proxy.hostname,proxy.port,timeout=3);c.request(method,path);r=c.getresponse();r.read();assert r.status==status,(path,r.status);c.close()
    Path(next(a.split('=',1)[1] for a in self.args if a.startswith('--screenshot='))).write_bytes(PNG+b'A'*1200);return 0
  with patch('capture.chrome_binary',return_value='/fake/chrome'),patch('capture.bounded_resolve',side_effect=resolve),patch('capture._request',side_effect=request),patch('subprocess.Popen',FakeChrome),patch('os.killpg'):
   raw,_=capture.chrome_screenshot('https://example.com/')
  self.assertTrue(raw.startswith(PNG));self.assertTrue(all(t[3]=='93.184.216.34' for t in calls));self.assertIn('--proxy-bypass-list=<-loopback>',arguments);self.assertIn('--disable-quic',arguments);self.assertIn('--force-webrtc-ip-handling-policy=disable_non_proxied_udp',arguments)
  profile=Path(next(a.split('=',1)[1] for a in arguments if a.startswith('--user-data-dir=')));self.assertFalse(profile.exists())
