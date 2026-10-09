"""Cover Studio P0-P3 review: real Store/API, disposable records, loopback port 0."""
import argparse,json,sys,tempfile,uuid
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from urllib.parse import urlsplit,parse_qs
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'desktop-app'))
import server
from storage import Store
parser=argparse.ArgumentParser();parser.add_argument('--count',type=int,choices=[36,1000],default=36);args=parser.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-cover-studio-'))
store=Store(root)
# Names/URLs are manual QA input, not harvested metadata. Website language/star
# fields are absent unless supplied; no invented stack or license information.
records=[
 dict(title='SHIJI',url='https://github.com/SilverLi123/shiji',category='开发工具',language='Swift · Python · JavaScript',tags=['SwiftUI','SQLite']),
 dict(title='React Bits',url='https://reactbits.dev/components',category='UI / 设计',tags=['组件','交互']),
 dict(title='Motion Sites',url='https://motionsites.ai/explore',category='视频',tags=['动效']),
 dict(title='为下一次创作留下线索',kind='prompt',category='灵感',snippet='从材料、光线与构图分析参考。记录可以复用的细节，并说明适合的使用场景。'),
 dict(title='保留真实代码缩进',kind='code',category='开发工具',language='JavaScript',snippet='async function saveIdea(input) {\n  const resource = await persist(input);\n  return {\n    id: resource.id,\n    saved: true\n  };\n}'),
 dict(title='从收藏到创作：为长期灵感管理建立清晰的界面节奏',url='https://www.recent.co/projects/olla-brand-identity-decentralised-finance',category='灵感'),
 dict(title='CPython',url='https://github.com/python/cpython',category='开发工具'),
 dict(title='VS Code',url='https://github.com/microsoft/vscode',category='开发工具'),
 dict(title='Poly Haven',url='https://polyhaven.com/',category='3D'),
 dict(title='声音也有空间',kind='file',category='音频'),
 dict(title='本地图片 · 用户指定封面',kind='file',category='美术素材'),
 dict(title='阅读与实验',kind='file',category='其他'),
 dict(title='Godot',url='https://github.com/godotengine/godot',category='开发工具'),
 dict(title='Astro',url='https://github.com/withastro/astro',category='开发工具'),
 dict(title='Rust',url='https://github.com/rust-lang/rust',category='开发工具'),
 dict(title='React',url='https://github.com/facebook/react',category='开发工具'),
 dict(title='Hugging Face',url='https://huggingface.co/models',category='开发工具'),
 dict(title='UI',kind='file',category='UI / 设计'),
 dict(title='字号、留白与色彩：一份关于中文排版和数字界面设计的观察笔记',kind='file',category='UI / 设计'),
 dict(title='Creative Engineering Resources for Designers Who Build',url='https://example.com/qa/long-english',category='灵感'),
 dict(title='拾集 SHIJI — Creative Engineering 与界面实验',url='https://example.com/qa/mixed',category='灵感'),
 dict(title='SuperLongRepositoryNameWithoutSpaces',url='https://github.com/SilverLi123/shiji/tree/feat/shiji-v2-card-restoration',category='开发工具'),
 dict(title='WWW iii · 不同字符宽度',kind='file',category='其他'),
 dict(title='布局与动态的连续性',url='https://example.com/qa/motion-2',category='视频'),
 dict(title='FRAME',url='https://example.com/qa/motion-3',category='视频'),
 dict(title='先保存，再完善',kind='code',category='开发工具',language='Python',snippet='def capture(url):\n    item = storage.save(url)\n    queue.enrich(item.id)\n    return item\n'),
 dict(title='色彩配置读取',kind='code',category='开发工具',language='Swift',snippet='struct Palette {\n    let background: Color\n    let foreground: Color\n}\n\nlet title = "拾集"'),
 dict(title='给创意一个具体的起点',kind='prompt',category='灵感',snippet='用简洁的语言写出作品的主视觉、材质、空间关系和光线。不要加入未经确认的品牌信息。'),
 dict(title='设计一个可读、可用、可持续收集的开发资源库',kind='prompt',category='灵感',snippet='为界面提出三种有明显差异的构图。每种都解释标题、留白和内容的关系。'),
 dict(title='环境声音参考',kind='file',category='音频'),
 dict(title='节奏与留白',kind='file',category='音频'),
 dict(title='设计文件合集',kind='file',category='其他'),
 dict(title='被保存的资料',kind='file',category='其他'),
 dict(title='错误图片回退 · 仍可阅读',url='https://example.com/qa/broken',category='UI / 设计',thumbnail='http://127.0.0.1:1/qa-missing.png'),
 dict(title='未命名边界（仅 QA 呈现测试）',url='https://example.com/qa/untitled',category='其他',notes='QA 比较页额外测试空名称渲染；实际 API 要求名称非空。'),
 dict(title='保持完整的非常长中文标题，同时测试关键词、换行、留白与装饰之间的关系，不让资源海报退回普通的统一占位卡片',kind='file',category='灵感')
]
if args.count==1000:
 records=[{**records[i%36], 'title':f'QA {i:04d} · '+records[i%36]['title'],'url':f'https://example.com/qa/{i}' if records[i%36].get('url') else '', 'thumbnail':''} for i in range(1000)]
for i,data in enumerate(records):
 data={'description':'隔离 QA 手动输入，用于视觉评审；不是网站抓取结果。',**data,'createdAt':(datetime(2026,10,9,tzinfo=timezone.utc)-timedelta(minutes=i)).isoformat()}
 with patch('storage.uuid.uuid4',return_value=uuid.uuid5(uuid.NAMESPACE_URL,'shiji-cover-studio-qa:'+str(i))):r=store.save(data)['resource']
 if i==10 and args.count==36:store.attachment(r['id'],(REPO/'desktop-app/static/previews/polyhaven.jpg').read_bytes(),{'name':'qa-local-preview.jpg','cover':True})
server.STORE=store
QA=Path(__file__).parent
class Handler(server.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/cover-studio':
   if not self.safe_request():return
   return self.send_bytes(200,(QA/'compare.html').read_bytes(),'text/html; charset=utf-8')
  assets={'/qa/baseline.js':'baseline.js','/qa/baseline.css':'baseline.css','/qa/compare.js':'compare.js','/qa/compare.css':'compare.css','/qa/metrics.js':'../../shiji-v2/card-restoration/qa/metrics.js'}
  if path in assets:
   if not self.safe_request():return
   file=QA/assets[path];return self.send_bytes(200,file.read_bytes(),'text/css' if file.suffix=='.css' else 'application/javascript')
  if path in ('/','/index.html'):
   if not self.safe_request():return
   html=(server.ROOT/'static/index.html').read_text().replace('</head>','<script src="/qa/metrics.js" defer></script></head>')
   return self.send_bytes(200,html.encode(),'text/html; charset=utf-8')
  if path=='/qa-frame':
   q=parse_qs(urlsplit(self.path).query)
   try:w=int(q.get('w',['390'])[0]);h=int(q.get('h',['900'])[0])
   except ValueError:return self.fail(400,'Invalid QA dimensions')
   if w not in [320,390,768,1024,1440] or not 600<=h<=1400:return self.fail(400,'Invalid QA dimensions')
   src='/cover-studio' if q.get('view',['app'])[0]=='compare' else '/#motion-stage'
   html=f'<!doctype html><html><head><title>Cover Studio {w}px QA</title><style>body{{margin:0;background:#303136}}iframe{{border:0;width:{w}px;height:{h}px;display:block}}</style></head><body><iframe title="SHIJI QA" src="{src}"></iframe></body></html>'
   return self.send_bytes(200,html.encode(),'text/html; charset=utf-8')
  return super().do_GET()
http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
state={'root':str(root),'port':http.server_port,'resources':len(records)}
(root/'qa-state.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
try:http.serve_forever()
finally:http.server_close()
