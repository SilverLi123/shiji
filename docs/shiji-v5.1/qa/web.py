"""Real HTTP/SQLite QA server with bounded opt-in trace, independent disposable data."""
import argparse,json,sys,tempfile,time
from pathlib import Path
from urllib.parse import urlsplit
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'desktop-app'))
import server
from storage import Store
p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=[0,100,1000,5000],default=1000);p.add_argument('--baseline',action='store_true');p.add_argument('--ab',choices=['normal','no-blur','no-ghost','no-stagger','stable-gutter'],default='normal');a=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-v51-web-'));store=Store(root)
for i in range(a.count):store.save(dict(title=f'QA {i:05d} · '+['开发资源与工具','代码与界面排版','长期灵感笔记'][i%3],kind=['website','code','prompt'][i%3],url=f'https://example.com/qa/{i}' if i%3==0 else '',category=['开发工具','UI / 设计','视频','灵感','3D'][i%5],language='JavaScript' if i%3==1 else '',snippet='function keepIdea(value) {\n  return value.trim();\n}' if i%3==1 else '隔离验收文字' if i%3==2 else '',description='真实 Store 保存的明确标记 QA 压力数据',tags=['QA']))
server.STORE=store
class Handler(server.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/':
   value=(REPO/'desktop-app/static/index.html').read_text().replace('<head>','<head><script src="/qa-trace.js"></script><script src="runtime-diagnostics.js"></script>',1).replace('</head>',('<style>.drawer-backdrop{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}</style></head>' if a.ab=='no-blur' else '<style>html{scrollbar-gutter:stable}</style></head>' if a.ab=='stable-gutter' else '</head>')).encode();mime='text/html;charset=utf-8'
  elif path=='/qa-trace.js':value=(Path(__file__).with_name('trace.js')).read_bytes();mime='application/javascript'
  elif path=='/resource-bits.js':
   import subprocess
   value=subprocess.check_output(['git','show','d7a6749:desktop-app/static/resource-bits.js'],cwd=REPO).decode() if a.baseline else (REPO/'desktop-app/static/resource-bits.js').read_text()
   value=value.replace('function layout(enter=false){','function layout(enter=false){const qaLayoutStart=performance.now();try{')
   value=value.replace('function schedule(){','function schedule(){',1)
   end=value.index('    function schedule(){');value=value[:end].rstrip()[:-1]+"}finally{window.ShijiQATrace?.emit('bits-layout',{renderMs:performance.now()-qaLayoutStart,gridWidth:grid.clientWidth});}}\n"+value[end:]
   value=value.encode();mime='application/javascript'
  elif path=='/app.js':
   import subprocess
   value=subprocess.check_output(['git','show','d7a6749:desktop-app/static/app.js'],cwd=REPO) if a.baseline else (REPO/'desktop-app/static/app.js').read_bytes()
   value+=b'\nconst qaDetailOriginal=detail;detail=function(...args){window.ShijiQATrace.begin();try{return qaDetailOriginal(...args);}finally{window.ShijiQATrace.end();}};'
   mime='application/javascript'
  elif path=='/shiji-v2-motion.js' and a.ab in ('no-stagger','no-ghost'):
   import subprocess
   value=subprocess.check_output(['git','show','d7a6749:desktop-app/static/shiji-v2-motion.js'],cwd=REPO).decode()
   if a.ab=='no-stagger':value=value.replace("stagger($('#drawer'),'.drawer-header h2,.detail-domain,.detail-actions,.detail-grid,.detail-block,.drawer-footer',detailAnimations);",'')
   if a.ab=='no-ghost':value=value.replace('if(!enabled()||!sourceElement||!detailElement)return;','if(true)return;')
   value=value.encode();mime='application/javascript'
  elif a.baseline and path.lstrip('/') in ('app.js','stable-cards.js','resource-bits.js','shiji-v2-motion.js'):
   import subprocess
   value=subprocess.check_output(['git','show','d7a6749:desktop-app/static/'+path.lstrip('/')],cwd=REPO);mime='application/javascript'
  else:return super().do_GET()
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(value)));self.end_headers();self.wfile.write(value)
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
print(json.dumps({'root':str(root),'port':http.server_port,'count':a.count,'baseline':a.baseline}),flush=True)
try:http.serve_forever()
finally:http.server_close()
