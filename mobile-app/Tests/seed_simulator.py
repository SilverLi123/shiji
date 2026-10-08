"""Seed only the explicitly owned Shiji iPhone QA simulator, never a physical device."""
import subprocess,json,uuid,hashlib,datetime,argparse
from pathlib import Path
parser=argparse.ArgumentParser(description='Seed synthetic data in an explicitly named QA simulator only')
parser.add_argument('--device',required=True,help='UDID of a simulator named Shiji iPhone QA')
UDID=parser.parse_args().device
devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json']))
assert any(d['udid']==UDID and d['name']=='Shiji iPhone QA' for values in devices['devices'].values() for d in values)
line=subprocess.check_output(['xcrun','simctl','get_app_container',UDID,'local.silver.shiji.mobile','groups'],text=True).strip()
root=Path(line.split('\t')[1])/'Library';assert UDID in str(root) and 'AppGroup' in str(root)
root.mkdir(parents=True,exist_ok=True);(root/'files').mkdir(exist_ok=True)
project=Path(__file__).resolve().parents[1]
items=[]
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for slug,title,url,category,description in [('recent','Recent — 品牌视觉与交互灵感','https://www.recent.co/','灵感','用色、版式与动效，留给下一次创作。'),('polyhaven','Poly Haven','https://polyhaven.com/','美术素材','HDRI、纹理与三维素材。'),('freesound','Freesound','https://freesound.org/','音频','声音素材与环境音。'),('reactbits','React Bits','https://reactbits.dev/','UI / 设计','界面组件与交互动效。'),('motionsites','MotionSites','https://motionsites.ai/','UI / 设计','网页构图与动态设计参考。')]:
 rid,aid=str(uuid.uuid4()),str(uuid.uuid4());data=(project.parent/'desktop-app/static/previews'/f'{slug}.jpg').read_bytes();(root/'files'/aid).write_bytes(data)
 a=dict(id=aid,resourceId=rid,name=f'{slug}.jpg',size=len(data),mime='image/jpeg',sha256=hashlib.sha256(data).hexdigest(),sourceUrl=url,license='待确认',licenseUrl='',author='',colors=[],createdAt=now,deleted=False)
 items.append(dict(id=rid,title=title,url=url,kind='website',category=category,description=description,notes='关注配色与页面动效。\n这是隔离模拟器的验收样例。',tags=['New, exact','品牌设计'],projects=['创作灵感'],projectNotes={'创作灵感':''},collection='创作灵感',colors=[],price='待确认',license='待确认',licenseUrl='',sourceUrl=url,author='',parentId='',coverId=aid,thumbnail='',favicon='',favorite=False,inbox=True,demo=False,deleted=False,createdAt=now,updatedAt=now,linkStatus='unchecked',linkCheckedAt='',attachments=[a]))
(root/'library.json').write_text(json.dumps(dict(version=1,schemaVersion=3,resources=items,collections=['创作灵感'],collectionMeta=[],smartCollections=[]),ensure_ascii=False))
(project/'build/qa-library-path.txt').write_text(str(root))
print('Seeded 5 synthetic QA records in owned iPhone simulator only')
