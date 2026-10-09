import sys,tempfile,json,argparse
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'desktop-app'))
import server
from storage import Store
parser=argparse.ArgumentParser(description='Isolated V3 integration QA: never opens the official library.')
parser.add_argument('--count',type=int,choices=[0,11,1000],default=11)
args=parser.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-v3-beta-qa-'))
store=Store(root)
records=[
 dict(title='SHIJI',url='https://github.com/SilverLi123/shiji',category='开发工具',language='Swift · Python · JavaScript',description='macOS 与 iPhone 资源库，使用 SwiftUI、WKWebView 和本地 SQLite。',tags=['SwiftUI','SQLite'],favorite=True),
 dict(title='React Bits',url='https://reactbits.dev/components',category='UI / 设计',description='收藏的前端组件与界面交互参考。',tags=['React','交互']),
 dict(title='Motion Sites',url='https://motionsites.ai/explore',category='视频',description='收藏的动态网页参考，用来研究节奏与转场。',tags=['动效','网页']),
 dict(title='让分类重排保持连续',kind='code',category='开发工具',language='JavaScript',snippet='function reorder(cards, positions) {\n  return cards.map((card, index) => {\n    const next = positions[index];\n    return {\n      id: card.id,\n      x: next.x, y: next.y\n    };\n  });\n}',tags=['JavaScript','New, exact']),
 dict(title='为下一次创作留下线索',kind='prompt',category='灵感',snippet='请从材料、光线与构图三个角度分析这张参考。保留作品中值得复用的细节，并说明它们适合的使用场景。',tags=['创作','构图']),
 dict(title='从收集到创作：关于界面节奏、内容层次与长期灵感管理的一份长标题笔记',url='https://www.recent.co/projects/olla-brand-identity-decentralised-finance',category='灵感',description='QA 自写笔记，用于测试长中文标题；网址来自用户收藏。',tags=['阅读','品牌']),
 dict(title='Poly Haven',url='https://polyhaven.com/',category='3D',description='现有固定时点的网站实际预览，验证图片优先。',tags=['3D','参考']),
 dict(title='本地图片参考',kind='file',category='美术素材',description='QA 使用仓库已有图片字节，验证附件封面优先。',tags=['图片']),
 dict(title='Freesound',url='https://freesound.org/browse/',category='音频',description='缺图时的音频素材类型封面。',tags=['音频','声音']),
 dict(title='Python Documentation',url='https://docs.python.org/3/',category='开发工具',description='文档入口，不补造技术指标与许可证。',tags=['Python']),
 dict(title='无法加载的封面',url='https://www.recent.co/projects',category='UI / 设计',thumbnail='http://127.0.0.1:1/qa-missing.png',description='QA 故意不可用的封面，验证错误回退。',tags=['错误恢复'])
]
if args.count==0:records=[]
if args.count==1000:
 records=[dict(title=f'QA {i:04d} · '+['真实字段工具卡片','保留缩进的代码片段','长期灵感的编辑式笔记'][i%3],kind=['website','code','prompt'][i%3],url=f'https://example.com/qa/{i}' if i%3==0 else '',category=['开发工具','UI / 设计','视频','灵感','音频'][i%5],language='JavaScript' if i%3==1 or i%15==0 else '',snippet='function keepIdea(value) {\n  return value.trim();\n}' if i%3==1 else 'QA 自写文字，用于测量真实持久化记录。' if i%3==2 else '',description='隔离压力夹具，不是用户或 Demo 数据。',tags=['QA fixture']) for i in range(1000)]
for data in reversed(records):
 r=store.save(data)['resource']
 if data.get('kind')=='file':store.attachment(r['id'],(REPO/'desktop-app/static/previews/polyhaven.jpg').read_bytes(),{'name':'qa-preview.jpg','cover':True})
server.STORE=store
class Handler(server.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if self.path.startswith('/qa-frame'):
   q=parse_qs(urlsplit(self.path).query);w=int(q.get('w',['390'])[0]);h=int(q.get('h',['844'])[0]);assert w in [390,768,1024,1440]
   page=f'<!doctype html><html><head><title>SHIJI isolated responsive QA</title><style>body{{margin:0;background:#303136;display:grid;justify-items:center}}iframe{{border:0;width:{w}px;height:{h}px}}</style></head><body><iframe title="SHIJI" src="/#resource-grid"></iframe></body></html>'
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(page.encode());return
  return super().do_GET()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
# This file contains only disposable QA coordinates, never real pairing credentials.
(root/'qa-state.json').write_text(json.dumps({'root':str(root),'port':http.server_port}))
print(json.dumps({'root':str(root),'port':http.server_port}),flush=True)
try:
 http.serve_forever()
finally:
 http.server_close()
 # Retained temp directory is disposable; never the official library.
