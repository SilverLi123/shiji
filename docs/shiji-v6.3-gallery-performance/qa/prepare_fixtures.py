"""Copy disposable V6.2 Store fixtures; add verified test image ratios and wide/long cards."""
import hashlib,json,shutil,sqlite3,struct,sys,tempfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'desktop-app'))
from storage import Store
root=Path(tempfile.mkdtemp(prefix='shiji-v63-fixtures-'));old=json.loads(Path('/tmp/shiji-v62-after.json').read_text());output={'root':str(root),'source':'copied V6.2 disposable fixture databases only','datasets':{}}
def png(width,height):
 def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
 rows=b''.join(b'\0'+b''.join(bytes((50+x*150//width,40+y*160//height,150)) for x in range(width)) for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
for size,info in old['datasets'].items():
 data=root/size;data.mkdir();origin=Path(info['data'])
 with sqlite3.connect(origin/'library.sqlite3') as a,sqlite3.connect(data/'library.sqlite3') as b:a.backup(b)
 shutil.copytree(origin/'files',data/'files');store=Store(data)
 with store.connect() as c:items=store._read_many(c,c.execute('SELECT * FROM resources ORDER BY id').fetchall())
 wide=long=images=0
 with store.connect() as c:
  for i,r in enumerate(items):
   changes={}
   if r['kind']=='website' and r['category']=='开发工具':changes['language']='TypeScript';wide+=1
   if i%91==0:changes['title']='长中文标题用于验证真实海报在动态尺寸与跨列布局中的换行、搜索高亮和辅助导航 · '+r['title'];long+=1
   if changes:store._write(c,changes,r)
 for i,r in enumerate(items):
  if r['attachments'] and not r['deleted']:
   dims=[(48,32),(32,64),(64,32)][i%3];store.attachment(r['id'],png(*dims),{'name':'QA ratio image.png','cover':True});images+=1
 store.flush_search();store.stop_search_worker()
 output['datasets'][size]={'data':str(data),'resources':len(items),'wide':wide,'longTitles':long,'variedImageCovers':images}
 Path('/tmp/shiji-v63-fixtures.json').write_text(json.dumps(output,indent=2));print(json.dumps(output['datasets'][size]),flush=True)
