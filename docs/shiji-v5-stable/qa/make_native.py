"""Create isolated ad-hoc native acceptance bundles with only QA credentials/data."""
import argparse,json,plistlib,shutil,socket,subprocess,sys,tempfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'desktop-app'))
from storage import Store
p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=[100,1000,5000],default=100);p.add_argument('--tag',default='instrument');args=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='shiji-v5-stable-qa-'));data=root/'data';store=Store(data)
for i in range(args.count):
 store.save(dict(title=f'QA {i:05d} · '+['开发资源与工具','代码与界面排版','长期灵感笔记'][i%3],kind=['website','code','prompt'][i%3],url=f'https://example.com/qa/{i}' if i%3==0 else '',category=['开发工具','UI / 设计','视频','灵感','3D'][i%5],language='JavaScript' if i%3==1 else '',snippet='function keepIdea(value) {\n  return value.trim();\n}' if i%3==1 else '隔离验收自写文字' if i%3==2 else '',description='明确标记的合成压力数据，通过真实 Store/SQLite 保存，不是 Demo 业务实现。',tags=['QA'],favorite=i%11==0))
app=root/f'Shiji Stable {args.count} Preview.app';shutil.copytree(REPO/'desktop-app/dist/Dev Resource Library.app',app)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
info=app/'Contents/Info.plist';meta=plistlib.loads(info.read_bytes());meta.update(CFBundleIdentifier=f'local.silver.shiji.stable-{args.count}-{args.tag}',CFBundleName=f'Shiji Stable {args.count} Preview',CFBundleDisplayName=f'拾集 Stable QA {args.count}',LSEnvironment={'SHIJI_PORT':str(port),'SHIJI_DATA_DIR':str(data),'SHIJI_PYTHON':sys.executable,'SHIJI_QA_METRICS':'1','SHIJI_SYNC_PORT':'0'});meta.pop('CFBundleURLTypes',None);info.write_bytes(plistlib.dumps(meta))
subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
state={'root':str(root),'app':str(app),'data':str(data),'port':port,'count':args.count,'tag':args.tag};Path(f'/tmp/shiji-v5-stable-{args.tag}-{args.count}.json').write_text(json.dumps(state));print(json.dumps(state))
