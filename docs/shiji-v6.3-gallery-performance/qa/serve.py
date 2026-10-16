"""Real Store/API/page on an ephemeral port, canonical fixtures copied from V6.2 QA only."""
import argparse,io,json,os,shutil,sqlite3,subprocess,sys,tarfile,tempfile,threading,time
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--size',choices=['1000','5000','20000','50000'],default='5000');p.add_argument('--before',action='store_true');p.add_argument('--cold',action='store_true');a=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-v63-qa-'));source=ROOT/'desktop-app'
if a.before:
 source=root/'source';source.mkdir()
 raw=subprocess.run(['git','archive','579d447:desktop-app'],cwd=ROOT,capture_output=True,check=True).stdout
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(source)
data=root/'data';data.mkdir();fixture=Path(json.loads(Path('/tmp/shiji-v63-fixtures.json').read_text())['datasets'][a.size]['data'])
with sqlite3.connect(fixture/'library.sqlite3') as old,sqlite3.connect(data/'library.sqlite3') as new:old.backup(new)
shutil.copytree(fixture/'files',data/'files')
if a.cold:
 with sqlite3.connect(data/'library.sqlite3') as c:
  for row in c.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'search_%'").fetchall():c.execute('DROP TRIGGER "'+row[0]+'"')
  for name in ('search_fts','search_docs','search_dirty','search_fts_dirty','search_meta'):c.execute('DROP TABLE IF EXISTS '+name)
sys.path.insert(0,str(source));import server
from storage import Store
local=threading.local()
class TimedStore(Store):
 def query_resources(self,body):
  start=time.perf_counter()
  try:return super().query_resources(body)
  finally:local.query_ms=(time.perf_counter()-start)*1000
server.STORE=TimedStore(data)
class Handler(server.Handler):
 def log_message(self,*args):pass
 def do_GET(self):
  if urlsplit(self.path).path=='/qa-v63.js':self.send_bytes(200,Path(__file__).with_name('probe.js').read_bytes(),'application/javascript');return
  if urlsplit(self.path).path=='/':
   self.send_bytes(200,(source/'static/index.html').read_text().replace('<head>','<head><script src="/qa-v63.js"></script>',1).encode(),'text/html; charset=utf-8');return
  return super().do_GET()
 def send_json(self,status,payload,attachment=False):
  start=time.perf_counter();raw=json.dumps(payload,ensure_ascii=False).encode();self.encoding_ms=(time.perf_counter()-start)*1000
  self.send_bytes(status,raw,'application/json; charset=utf-8','shiji-bookmarks.json' if attachment else None)
 def end_headers(self):
  if urlsplit(self.path).path=='/api/query':self.send_header('Server-Timing',f'query;dur={getattr(local,"query_ms",0):.3f},json;dur={getattr(self,"encoding_ms",0):.3f}')
  return super().end_headers()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
state={'root':str(root),'data':str(data),'source':str(source),'before':a.before,'cold':a.cold,'size':int(a.size),'port':http.server_port,'url':f'http://127.0.0.1:{http.server_port}/','pid':os.getpid()}
Path('/tmp/shiji-v63-'+('before' if a.before else 'after')+'-'+a.size+('-cold' if a.cold else '')+'.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
try:http.serve_forever()
finally:server.STORE.stop_search_worker();http.server_close()
