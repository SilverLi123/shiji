"""Disposable real HTTP/SQLite browser comparison; diagnostics endpoint exists only here."""
import json,sys,tempfile
from pathlib import Path
from urllib.parse import urlsplit
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'desktop-app'))
import server
from storage import Store
root=Path(tempfile.mkdtemp(prefix='shiji-v52-web-'));server.STORE=Store(root)
for i in range(1000):server.STORE.save(dict(title=f'QA {i:05d} · '+['开发资源与工具','代码与界面排版','长期灵感笔记'][i%3],kind=['website','code','prompt'][i%3],url=f'https://example.com/qa/{i}' if i%3==0 else '',category=['开发工具','UI / 设计','视频','灵感','3D'][i%5],language='JavaScript' if i%3==1 else '',snippet='function keepIdea(value) {\n  return value.trim();\n}' if i%3==1 else '隔离验收自写文字' if i%3==2 else '',description='临时 Store 保存的标记 QA 压力资源',tags=['QA']))
class Handler(server.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/':value=(REPO/'desktop-app/static/index.html').read_text().replace('<head>','<head><script>window.ShijiNative=true;</script><script src="/qa-v52-probe.js"></script>',1).encode();mime='text/html;charset=utf-8'
  elif path=='/qa-v52-probe.js':value=Path(__file__).with_name('probe.js').read_bytes();mime='application/javascript'
  elif path=='/app.js':value=(REPO/'desktop-app/static/app.js').read_bytes()+b'\nconst qaDetailOriginal=detail;detail=function(...args){window.ShijiQATrace.begin();try{return qaDetailOriginal(...args);}finally{window.ShijiQATrace.end();}};';mime='application/javascript'
  else:return super().do_GET()
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(value)));self.end_headers();self.wfile.write(value)
 def do_POST(self):
  if urlsplit(self.path).path!='/api/qa-v52-result':return super().do_POST()
  if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}'):self.send_error(403);return
  n=int(self.headers.get('Content-Length','0'))
  if not 0<n<=65536:self.send_error(400);return
  row=json.loads(self.rfile.read(n));row['received']=__import__('time').time()
  with (root/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  self.send_response(204);self.end_headers()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'root':str(root),'port':http.server_port}),flush=True)
try:http.serve_forever()
finally:http.server_close()
