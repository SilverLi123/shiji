"""Optional TLS-only LAN listener, one-use pairing and revocable device tokens."""
import base64,hashlib,hmac,ipaddress,json,os,secrets,socket,ssl,subprocess,threading,time
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from mobile_sync import SyncEngine,RevisionConflict,MAX_FILE

def local_addresses():
 candidates={'127.0.0.1'}
 if Path('/sbin/ifconfig').exists():
  output=subprocess.check_output(['/sbin/ifconfig'],text=True)
  for line in output.splitlines():
   parts=line.strip().split()
   if len(parts)>1 and parts[0]=='inet':
    try:
     address=ipaddress.ip_address(parts[1])
     if isinstance(address,ipaddress.IPv4Address) and any(address in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')):candidates.add(str(address))
    except ValueError:pass
 return sorted(candidates,key=lambda v:(v=='127.0.0.1',v))

class TLSServer(ThreadingHTTPServer):
 daemon_threads=True
 def server_bind(self):
  # HTTPServer resolves wildcard hostnames synchronously; LAN sync uses IPs only.
  TCPServer.server_bind(self)
  self.server_name="Shiji local sync";self.server_port=self.server_address[1]
 def get_request(self):
  sock,address=self.socket.accept();sock.settimeout(15)
  try:return self.context.wrap_socket(sock,server_side=True,do_handshake_on_connect=False),address
  except Exception:sock.close();raise

class SyncService:
 def __init__(self,store,port=8784,bind='0.0.0.0'):
  self.store=store;self.engine=SyncEngine(store);self.port=port;self.bind=bind;self.http=None;self.lock=threading.RLock();self.pair_secret='';self.pair_until=0;self.attempts={}
  self.root=store.root/'mobile-sync';self.root.mkdir(exist_ok=True,mode=0o700);self.root.chmod(0o700)
  self.config_file=self.root/'devices.json'
  self.devices=json.loads(self.config_file.read_text()) if self.config_file.exists() else {}
 def _write_devices(self):
  tmp=self.root/'devices.tmp';tmp.write_text(json.dumps(self.devices));tmp.chmod(0o600);tmp.replace(self.config_file)
 def _certificate(self,addresses):
  cert=self.root/'certificate.pem';key=self.root/'private-key.pem';config=self.root/'certificate.conf';ca=self.root/'authority.pem';ca_key=self.root/'authority-key.pem';csr=self.root/'request.csr';profile=self.root/'certificate-profile.json'
  expected={'version':2,'addresses':sorted(addresses)}
  try:current=json.loads(profile.read_text())
  except (OSError,ValueError):current=None
  expires_soon=cert.exists() and subprocess.run(['/usr/bin/openssl','x509','-checkend',str(7*86400),'-noout','-in',str(cert)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
  renew=current!=expected or expires_soon
  if renew or not cert.exists() or not key.exists() or not ca.exists() or not ca_key.exists():
   self.certificate_renewed=cert.exists()
   san=','.join('IP:'+a for a in addresses)
   config.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN=Shiji local sync\n[ext]\nsubjectAltName='+san+'\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n')
   config.chmod(0o600)
   def run(*args):subprocess.run(['/usr/bin/openssl',*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   root_config=self.root/'authority.conf';root_config.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN=Shiji private sync authority\n[ext]\nbasicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n')
   try:
    run('req','-sha256','-x509','-newkey','ec','-pkeyopt','ec_paramgen_curve:prime256v1','-pkeyopt','ec_param_enc:named_curve','-nodes','-days','3650','-config',str(root_config),'-keyout',str(ca_key),'-out',str(ca))
    run('req','-sha256','-new','-newkey','rsa:2048','-nodes','-config',str(config),'-keyout',str(key),'-out',str(csr))
    run('x509','-sha256','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(ca_key),'-set_serial',str(secrets.randbits(120)+1),'-days','365','-extfile',str(config),'-extensions','ext','-out',str(cert))
   finally:
    for p in (config,root_config,csr):p.unlink(missing_ok=True)
   for p in (key,cert,ca,ca_key):p.chmod(0o600)
   profile.write_text(json.dumps(expected));profile.chmod(0o600)
  return cert,key
 def start(self):
  with self.lock:
   if self.http:return self.status()
   addresses=local_addresses();cert,key=self._certificate(addresses)
   context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(cert,key)
   # Apple's bundled Python/LibreSSL requires an explicit ECDHE curve for EC keys.
   context.set_ecdh_curve('prime256v1')
   http=TLSServer((self.bind,self.port),SyncHandler);http.context=context;http.service=self;self.http=http;self.addresses=addresses;self.der=ssl.PEM_cert_to_DER_cert(cert.read_text())
   self.authority_der=ssl.PEM_cert_to_DER_cert((self.root/'authority.pem').read_text());threading.Thread(target=http.serve_forever,name='ShijiSyncTLS',daemon=True).start()
   return self.status()
 def stop(self):
  with self.lock:
   http=self.http;self.http=None;self.pair_secret='';self.pair_until=0
  if http:http.shutdown();http.server_close()
 def status(self):
  with self.lock:return {'enabled':self.http is not None,'certificateRenewed':getattr(self,'certificate_renewed',False),'pairingAvailable':bool(self.pair_secret) and time.time()<self.pair_until,'port':self.http.server_port if self.http else self.port,'addresses':getattr(self,'addresses',[]),'devices':[{'id':key,'name':value['name']} for key,value in self.devices.items()],'libraryId':self.engine.library_id}
 def pairing(self,address=None):
  with self.lock:
   if not self.http:raise ValueError('请先开启电脑同步。')
   address=address or self.addresses[0]
   if address not in self.addresses:raise ValueError('请选择这台电脑的局域网地址。')
   self.pair_secret=secrets.token_urlsafe(32);self.pair_until=time.time()+300
   return {'code':'shiji-sync://pair?'+urlencode({'v':'1','address':address,'port':self.http.server_port,'certificate':base64.b64encode(self.der).decode(),'authority':base64.b64encode(self.authority_der).decode(),'secret':self.pair_secret}),'expiresIn':300,'address':address,'port':self.http.server_port}
 def pair(self,body):
  with self.lock:
   if not isinstance(body,dict) or set(body)!={'secret','deviceId','name'} or not isinstance(body.get('secret'),str) or not self.pair_secret or time.time()>self.pair_until or not hmac.compare_digest(body['secret'],self.pair_secret):raise PermissionError('配对码已失效，请在电脑生成新码。')
   device=body['deviceId'];name=body['name']
   if not isinstance(device,str) or len(device)!=36 or not isinstance(name,str) or not name.strip() or len(name)>80:raise ValueError('设备信息无效。')
   token=secrets.token_urlsafe(32)
   old=self.devices.copy();self.devices={**self.devices,device:{'name':name.strip(),'tokenHash':hashlib.sha256(token.encode()).hexdigest()}}
   try:self._write_devices()
   except Exception:self.devices=old;raise
   self.pair_secret='';self.pair_until=0
   return {'version':1,'token':token,'libraryId':self.engine.library_id,'computerName':socket.gethostname()[:80]}
 def authenticated(self,header):
  if not isinstance(header,str) or not header.startswith('Bearer '):return False
  hashed=hashlib.sha256(header[7:].encode()).hexdigest()
  with self.lock:return any(hmac.compare_digest(hashed,d['tokenHash']) for d in self.devices.values())
 def revoke(self):
  with self.lock:self.devices={};self._write_devices();self.pair_secret='';self.pair_until=0

class SyncHandler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*_):pass # Tokens, pairing codes and resource text are never logged.
 def handle(self):
  try:super().handle()
  except (ssl.SSLError,ConnectionError,TimeoutError):pass
 def send(self,status,value,kind='application/json; charset=utf-8'):
  raw=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def read(self,limit):
  if self.headers.get('Transfer-Encoding'):raise ValueError('不支持分块上传。')
  length=self.headers.get('Content-Length','')
  if not length.isdecimal() or not 0<int(length)<=limit:raise ValueError('请求大小无效或超过上限。')
  raw=self.rfile.read(int(length))
  if len(raw)!=int(length):raise ValueError('上传中断，请重试。')
  return raw
 def json(self,limit):
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('请提交 JSON。')
  return json.loads(self.read(limit))
 def dispatch(self):
  service=self.server.service;path=urlsplit(self.path).path
  # Browser-origin requests have no access to this native device protocol.
  if self.headers.get('Origin'):self.close_connection=True;self.send(403,{'error':'仅供已配对 App 使用。'});return
  try:
   if self.command=='POST' and path=='/sync/pair':
    now=time.time();peer=self.client_address[0]
    with service.lock:
     count,started=service.attempts.get(peer,(0,now))
     if now-started>60:count,started=0,now
     if count>=10:self.close_connection=True;self.send(429,{'error':'配对尝试过多，请稍后重试。'});return
     service.attempts[peer]=(count+1,started)
    self.send(200,service.pair(self.json(8192)));return
   if not service.authenticated(self.headers.get('Authorization','')):self.close_connection=True;self.send(401,{'error':'设备未配对或已解除，请重新配对。'});return
   if self.command=='GET' and path=='/sync/snapshot':self.send(200,service.engine.snapshot())
   elif self.command=='GET' and path.startswith('/sync/files/'):
    raw,_=service.engine.file(path.rsplit('/',1)[1]);self.send(200,raw,'application/octet-stream')
   elif self.command=='PUT' and path.startswith('/sync/files/'):
    service.engine.stage(path.rsplit('/',1)[1],self.read(MAX_FILE),self.headers.get('X-Shiji-SHA256',''));self.send(200,{'ok':True})
   elif self.command=='POST' and path=='/sync/commit':self.send(200,service.engine.commit(self.json(64*1024*1024)))
   else:self.send(404,{'error':'同步接口不存在。'})
  except PermissionError as e:self.close_connection=True;self.send(403,{'error':str(e)})
  except RevisionConflict as e:self.send(409,{'error':str(e)})
  except (ValueError,KeyError,TypeError) as e:self.close_connection=True;self.send(400,{'error':str(e)})
  except (OSError,Exception):self.close_connection=True;self.send(500,{'error':'同步暂时无法保存，请检查电脑磁盘后重试。'})
 do_GET=dispatch
 do_POST=dispatch
 do_PUT=dispatch
