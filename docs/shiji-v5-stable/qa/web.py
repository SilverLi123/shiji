"""Existing real desktop app plus an opt-in metrics script; disposable databases only."""
import argparse,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlsplit
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'desktop-app'))
import server
from storage import Store
p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=[100,1000,5000],required=True);a=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-v5-perf-web-'));store=Store(root)
for i in range(a.count):store.save(dict(title=f'QA {i:05d} · '+['开发资源与工具','代码与界面排版','长期灵感笔记'][i%3],kind=['website','code','prompt'][i%3],url=f'https://example.com/qa/{i}' if i%3==0 else '',category=['开发工具','UI / 设计','视频','灵感','3D'][i%5],language='JavaScript' if i%3==1 else '',snippet='function keepIdea(value) {\n  return value.trim();\n}' if i%3==1 else '明确标记的隔离验收文字' if i%3==2 else '',description='通过真实 Store 保存的压力夹具',tags=['QA'],favorite=i%11==0))
server.STORE=store
class Handler(server.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/':
   page=(REPO/'desktop-app/static/index.html').read_text().replace('<head>','<head><script src="runtime-diagnostics.js"></script>',1)
   body=page.encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
  super().do_GET()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
state={'root':str(root),'port':http.server_port,'count':a.count};Path(f'/tmp/shiji-v5-web-{a.count}.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
try:http.serve_forever()
finally:http.server_close()
