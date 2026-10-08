import json,os,socket,subprocess,sys,tempfile,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
class DesktopServiceTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.children=[]
 def tearDown(self):
  for child in self.children:
   if child.poll() is None:child.terminate();child.wait(timeout=15)
   child.stdout.close();child.stderr.close()
  self.temp.cleanup()
 def start(self,port=0):
  child=subprocess.Popen([sys.executable,str(ROOT/'desktop_service.py'),'--data-dir',str(self.root),'--port',str(port),'--instance','test-instance'],env={**os.environ,'SHIJI_SYNC_PORT':'0'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);self.children.append(child)
  line=child.stdout.readline()
  if not line.startswith('READY '):self.fail(line+child.stderr.read())
  self.base='http://127.0.0.1:'+line.split()[1];return child
 def request(self,path,body=None,token=None,origin=None):
  headers={}
  if token:headers['Authorization']='Bearer '+token
  if origin:headers['Origin']=origin
  if body is not None:headers['Content-Type']='application/json'
  with urlopen(Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers),timeout=4) as response:return json.load(response)
 def test_capture_pairing_duplicate_and_restart(self):
  child=self.start();self.assertEqual(self.request('/api/desktop-status')['instance'],'test-instance')
  token=self.request('/api/pairing')['token'];origin='chrome-extension://'+'a'*32
  self.assertTrue(self.request('/api/clip/ping',{},token,origin)['connected'])
  with self.assertRaises(HTTPError) as error:self.request('/api/clip/ping',{},'bad',origin)
  self.assertEqual(error.exception.code,403)
  with self.assertRaises(HTTPError):self.request('/api/clip',{'url':'https://example.com/'},token,'https://evil.example')
  page={'url':'https://example.com/resource','title':'Captured resource','selection':'Selected text'}
  self.request('/api/clip',page,token,origin);self.request('/api/clip',page,token,origin)
  resources=self.request('/api/resources')['resources'];self.assertEqual(len(resources),1);self.assertIn('Selected text',resources[0]['notes'])
  child.terminate();child.wait(timeout=15);self.start();self.assertEqual(len(self.request('/api/resources')['resources']),1)
 def test_port_collision_does_not_create_database(self):
  with socket.socket() as reserved:
   reserved.bind(('127.0.0.1',0));reserved.listen()
   child=subprocess.Popen([sys.executable,str(ROOT/'desktop_service.py'),'--data-dir',str(self.root),'--port',str(reserved.getsockname()[1]),'--instance','collision'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);self.children.append(child)
   child.communicate(timeout=10);self.assertNotEqual(child.returncode,0);self.assertFalse((self.root/'library.sqlite3').exists())
 def test_second_app_refuses_same_library(self):
  self.start();child=subprocess.Popen([sys.executable,str(ROOT/'desktop_service.py'),'--data-dir',str(self.root),'--port','0','--instance','second'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);self.children.append(child)
  _,error=child.communicate(timeout=10);self.assertNotEqual(child.returncode,0);self.assertIn('另一个 App',error)
 def test_mobile_sync_control_default_off_and_origin_guard(self):
  child=self.start();self.assertFalse(self.request('/api/mobile-sync')['enabled'])
  with self.assertRaises(HTTPError) as denied:self.request('/api/mobile-sync/enable',{},origin='https://evil.example')
  self.assertEqual(denied.exception.code,403);self.assertFalse(self.request('/api/mobile-sync')['enabled'])
  status=self.request('/api/mobile-sync/enable',{});self.assertTrue(status['enabled']);self.assertGreater(status['port'],0)
  code=self.request('/api/mobile-sync/pair',{'address':'127.0.0.1'})['code'];self.assertTrue(code.startswith('shiji-sync://pair?'))
  self.assertTrue(self.request('/api/mobile-sync')['pairingAvailable'])
  self.assertFalse(self.request('/api/mobile-sync/revoke',{})['pairingAvailable'])
  self.assertFalse(self.request('/api/mobile-sync/stop',{})['enabled'])
  child.terminate();child.wait(timeout=15);self.start();self.assertFalse(self.request('/api/mobile-sync')['enabled'])
if __name__=='__main__':unittest.main()
