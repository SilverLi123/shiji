import json,ssl,tempfile,time,unittest,uuid
from http.client import HTTPSConnection
from urllib.parse import urlsplit,parse_qs
from storage import Store
from sync_transport import SyncService

class SyncTransportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.service=SyncService(Store(self.tmp.name),port=0,bind='127.0.0.1');self.service.start();self.addCleanup(self.service.stop)
  self.context=ssl.create_default_context(cafile=str(self.service.root/'authority.pem'))
 def request(self,method,path,body=None,headers=None):
  connection=HTTPSConnection('127.0.0.1',self.service.http.server_port,context=self.context,timeout=5)
  raw=json.dumps(body) if body is not None else None
  values={'Content-Type':'application/json',**(headers or {})}
  connection.request(method,path,raw,values);response=connection.getresponse();data=response.read();connection.close();return response.status,json.loads(data)
 def pair(self):
  code=self.service.pairing('127.0.0.1')['code'];secret=parse_qs(urlsplit(code).query)['secret'][0]
  body={'secret':secret,'deviceId':str(uuid.uuid4()),'name':'Test iPhone'}
  status,response=self.request('POST','/sync/pair',body);self.assertEqual(status,200);return body,response
 def test_tls_pair_single_use_revoke_and_restart(self):
  body,result=self.pair();headers={'Authorization':'Bearer '+result['token']}
  self.assertEqual(self.request('POST','/sync/pair',body)[0],403)
  self.assertEqual(self.request('GET','/sync/snapshot',headers=headers)[0],200)
  self.service.revoke();self.assertEqual(self.request('GET','/sync/snapshot',headers=headers)[0],401)
  self.assertNotIn(result['token'],self.service.config_file.read_text())
 def test_expiry_origin_and_missing_token(self):
  code=self.service.pairing('127.0.0.1')['code'];self.service.pair_until=time.time()-1
  body={'secret':parse_qs(urlsplit(code).query)['secret'][0],'deviceId':str(uuid.uuid4()),'name':'Phone'}
  self.assertEqual(self.request('POST','/sync/pair',body)[0],403)
  self.assertEqual(self.request('GET','/sync/snapshot')[0],401)
  _,paired=self.pair();self.assertEqual(self.request('GET','/sync/snapshot',headers={'Authorization':'Bearer '+paired['token'],'Origin':'https://evil.example'})[0],403)
 def test_unknown_certificate_fails_normal_tls_verification(self):
  client=HTTPSConnection('127.0.0.1',self.service.http.server_port,context=ssl.create_default_context(),timeout=5)
  with self.assertRaises(ssl.SSLCertVerificationError):client.request('GET','/sync/snapshot')
  client.close()

 def test_certificate_renews_for_changed_address_and_is_stable_otherwise(self):
  import subprocess
  first=self.service.der;cert,_=self.service._certificate(['127.0.0.1','192.168.1.10']);changed=cert.read_bytes()
  self.assertNotEqual(ssl.PEM_cert_to_DER_cert(cert.read_text()),first)
  self.service._certificate(['127.0.0.1','192.168.1.10']);self.assertEqual(cert.read_bytes(),changed)
  self.service._certificate(['127.0.0.1','192.168.1.11']);self.assertNotEqual(cert.read_bytes(),changed)
  decoded=ssl._ssl._test_decode_cert(str(cert));ssl.match_hostname(decoded,'192.168.1.11')
  with self.assertRaises(ssl.CertificateError):ssl.match_hostname(decoded,'192.168.1.10')
  authority=subprocess.check_output(['/usr/bin/openssl','x509','-in',str(self.service.root/'authority.pem'),'-text','-noout'],text=True)
  self.assertIn('ASN1 OID: prime256v1',authority)
