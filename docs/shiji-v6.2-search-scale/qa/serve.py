"""Identical copied V6.1 fixtures, random port, real backend/UI, metadata-only QA probe."""
import argparse,json,sys,tempfile,sqlite3,shutil,os
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--size',default='1000',choices=['0','1000','5000','20000','50000']);p.add_argument('--before',action='store_true');args=p.parse_args()
baseline=json.loads(Path('/tmp/shiji-v62-before.json').read_text());source=Path(baseline['source']) if args.before else ROOT/'desktop-app';sys.path.insert(0,str(source));import server
from storage import Store
root=Path(tempfile.mkdtemp(prefix='shiji-v62-web-'));data=root/'data';data.mkdir()
if args.size!='0':
 with sqlite3.connect(Path(baseline['datasets'][args.size]['data'])/'library.sqlite3') as c,sqlite3.connect(data/'library.sqlite3') as d:c.backup(d)
 shutil.copytree(Path(baseline['datasets'][args.size]['data'])/'files',data/'files')
server.STORE=Store(data)
class Handler(server.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/':raw=(source/'static/index.html').read_text().replace('<head>','<head><script src="/qa-v62.js"></script>',1).encode();mime='text/html; charset=utf-8'
  elif path=='/qa-v62.js':raw=Path(__file__).with_name('probe.js').read_bytes();mime='application/javascript'
  else:return super().do_GET()
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  if urlsplit(self.path).path!='/api/qa-v62':return super().do_POST()
  if not self.safe_request():return
  row=json.loads(self.read_bytes(160000));(root/'metrics.json').write_text(json.dumps(row));self.send_response(204);self.end_headers()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
label=('before' if args.before else 'after')+'-'+args.size
state={'root':str(root),'data':str(data),'pid':os.getpid(),'port':http.server_port,'url':f'http://127.0.0.1:{http.server_port}/','source':str(source),'label':label}
Path('/tmp/shiji-v62-web-'+label+'.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
try:http.serve_forever()
finally:
 if hasattr(server.STORE,'stop_search_worker'):server.STORE.stop_search_worker()
 http.server_close()
