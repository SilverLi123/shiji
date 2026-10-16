"""Real capture commits while querying copied indexed Store fixtures; network is deterministic."""
import json,sys,sqlite3,shutil,tempfile,time,threading,statistics
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'desktop-app'))
from storage import Store
from quick_capture import fallback_title
source=json.loads(Path('/tmp/shiji-v62-after.json').read_text());output={}
for size in ('1000','5000'):
 root=Path(tempfile.mkdtemp(prefix='shiji-v62-concurrent-'));data=root/'data';data.mkdir();old=Path(source['datasets'][size]['data'])
 with sqlite3.connect(old/'library.sqlite3') as a,sqlite3.connect(data/'library.sqlite3') as b:a.backup(b)
 shutil.copytree(old/'files',data/'files');store=Store(data);store.flush_search()
 # Remove only disposable fixture backlog from the copy, then drive actual capture lifecycle.
 with store.connect() as c:c.execute("UPDATE capture_jobs SET status='cancelled',lease='',lease_until=0 WHERE status IN ('pending','running','retry')")
 ids=[]
 for i in range(20):
  url=f'https://example.com/concurrent-{i}';ids.append(store.save({'url':url,'title':fallback_title(url),'inbox':True})['resource']['id'])
 store.capture_action({'action':'resume'});store.save({'title':'manualpreserved'},ids[0]);errors=[];samples=[]
 def fetch(item,*args):
  time.sleep(.01) # Controlled network fixture latency, never a product delay.
  return {'metadata':{'title':'captureindexed '+item['id'],'description':'自动补全索引'}}
 def work():
  try:
   for _ in range(20):store.capture_step()
  except Exception as e:errors.append(str(e))
 with patch('capture_jobs.fetch_payload',side_effect=fetch):
  t=threading.Thread(target=work);t.start()
  while t.is_alive() or len(samples)<30:
   start=time.perf_counter();page=store.query_resources({'filters':{'search':'React 动效'}});samples.append((time.perf_counter()-start)*1000)
   assert page['total']>0
  t.join()
 assert not errors,errors
 assert store.get(ids[0])['title']=='manualpreserved'
 assert store.query_resources({'filters':{'search':'captureindexed'}})['total']==19
 assert all(store.get(rid) for rid in ids)
 ordered=sorted(samples);output[size]={'samplesMs':samples,'p50Ms':statistics.median(samples),'p95Ms':ordered[min(len(ordered)-1,int(len(ordered)*.95))],'captureCompleted':19,'manualEditSkipped':1,'resourcesLost':0}
 store.stop_search_worker()
Path('/tmp/shiji-v62-concurrent.json').write_text(json.dumps(output,indent=2));print(json.dumps(output))
