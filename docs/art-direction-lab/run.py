"""Read-only art review; always creates disposable SQLite, binds loopback port 0."""
from pathlib import Path
import sys,tempfile,json,uuid,mimetypes
from unittest.mock import patch
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'desktop-app'))
from storage import Store
LAB=Path(__file__).parent
FIXTURES=[
 ('shiji',0,'开发工具','折叠品牌框',dict(title='SHIJI',url='https://github.com/SilverLi123/shiji',category='开发工具',language='Swift · Python · JavaScript',tags=['SwiftUI','SQLite'])),
 ('vscode',7,'开发工具','编辑器透视',dict(title='VS Code',url='https://github.com/microsoft/vscode',category='开发工具')),
 ('godot',12,'开发工具','等距几何舞台',dict(title='Godot',url='https://github.com/godotengine/godot',category='开发工具')),
 ('react',1,'设计灵感','组件字体标本',dict(title='React Bits',url='https://reactbits.dev/components',category='UI / 设计',tags=['组件','交互'])),
 ('olla',5,'设计灵感','双色印刷纸页',dict(title='Recent — Olla',url='https://www.recent.co/projects/olla-brand-identity-decentralised-finance',category='灵感')),
 ('motion',2,'动效 / 3D','动态字带',dict(title='Motion Sites',url='https://motionsites.ai/explore',category='视频',tags=['动效'])),
 ('polyhaven',8,'动效 / 3D','实际网站预览',dict(title='Poly Haven',url='https://polyhaven.com/',category='3D')),
 ('hugging',16,'AI / ML','曲面拓扑',dict(title='Hugging Face',url='https://huggingface.co/models',category='开发工具')),
 ('pytorch',37,'AI / ML','透明张量切片',dict(title='PyTorch',url='https://pytorch.org/',category='开发工具')),
 ('article',38,'技术文章','变换字体的纸上实验',dict(title='CSS transform',url='https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform',category='开发工具')),
 ('code',4,'代码','真实代码的光学层级',dict(title='保留真实代码缩进',kind='code',category='开发工具',language='JavaScript',snippet='async function saveIdea(input) {\n  const resource = await persist(input);\n  return {\n    id: resource.id,\n    saved: true\n  };\n}')),
 ('prompt',3,'Prompt','折页创作简报',dict(title='为下一次创作留下线索',kind='prompt',category='灵感',snippet='从材料、光线与构图分析参考。记录可以复用的细节，并说明适合的使用场景。')),
]
def dataset(root):
 store=Store(root);items=[]
 for key,index,group,direction,data in FIXTURES:
  with patch('storage.uuid.uuid4',return_value=uuid.uuid5(uuid.NAMESPACE_URL,'shiji-cover-studio-qa:'+str(index))):
   r=store.save({'description':'隔离测试手动输入，不代表网站抓取结果。',**data})['resource']
  if key=='polyhaven':
   store.attachment(r['id'],(REPO/'desktop-app/static/previews/polyhaven.jpg').read_bytes(),{'name':'existing-polyhaven-website-preview.jpg','cover':True})
   r=store.get(r['id'])
  items.append(dict(master=key,group=group,direction=direction,resource=r))
 return store,items

def make_server():
 root=Path(tempfile.mkdtemp(prefix='shiji-art-direction-lab-'));store,items=dataset(root)
 routes={'/':LAB/'index.html','/lab.css':LAB/'lab.css','/lab.js':LAB/'lab.js',
 '/compare2.js':REPO/'desktop-app/static/shiji-v2.js','/compare2.css':REPO/'desktop-app/static/shiji-v2.css',
 '/restoration.js':REPO/'docs/cover-studio-2/qa/baseline.js','/restoration.css':REPO/'docs/cover-studio-2/qa/baseline.css',
 '/polyhaven.jpg':REPO/'desktop-app/static/previews/polyhaven.jpg'}
 for kind in ['v3-poster-lab','v5-spatial-poster']:
  for name in ['index.html','desktop.png','motion.mp4']:
   routes[f'/reference/{kind}/{name}']=REPO/'docs/shiji-v2/reference'/kind/name
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   path=urlsplit(self.path).path
   if path=='/lab-data':
    data=json.dumps(items,ensure_ascii=False).encode();mime='application/json'
   elif path in routes:
    file=routes[path];data=file.read_bytes();mime=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8' if mime.startswith('text/') else mime)
   self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
  def do_POST(self):self.send_error(405,'Read-only visual review')
  do_PUT=do_DELETE=do_PATCH=do_POST
  def log_message(self,*args):pass
 http=ThreadingHTTPServer(('127.0.0.1',0),Handler);http.lab_root=root;http.store=store
 return http
if __name__=='__main__':
 http=make_server();print(json.dumps({'url':f'http://127.0.0.1:{http.server_port}/','temporary_data':str(http.lab_root),'resources':12}),flush=True)
 try:http.serve_forever()
 finally:http.server_close()
