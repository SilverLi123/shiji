"""Same-data, multi-round after measurements. Only copied disposable baselines."""
import json,sys,tempfile,shutil,sqlite3,time,statistics,platform,resource
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'desktop-app'))
from storage import Store
before=json.loads(Path('/tmp/shiji-v62-before.json').read_text());root=Path(tempfile.mkdtemp(prefix='shiji-v62-after-'))
result={'source':str(ROOT),'beforeCommit':before['sourceCommit'],'environment':before['environment'],'root':str(root),'datasets':{}}
def sample(fn,n=9):
 times=[];value=None
 for _ in range(n):
  start=time.perf_counter();value=fn();times.append((time.perf_counter()-start)*1000)
 return {'samplesMs':times,'p50Ms':statistics.median(times),'p95Ms':sorted(times)[min(n-1,int(n*.95))]},value
for count,info in before['datasets'].items():
 directory=root/count;directory.mkdir()
 with sqlite3.connect(Path(info['data'])/'library.sqlite3') as c,sqlite3.connect(directory/'library.sqlite3') as d:c.backup(d)
 shutil.copytree(Path(info['data'])/'files',directory/'files',copy_function=shutil.copy2)
 start=time.perf_counter();store=Store(directory)
 with patch.object(store,'_schedule_fts'):
  meta=store.library_metadata();first=store.query_resources({});first_usable=(time.perf_counter()-start)*1000
  fallback_start=time.perf_counter();fallback=store.query_resources({'filters':{'search':'动效'}});fallback_ms=(time.perf_counter()-fallback_start)*1000
 start=time.perf_counter();store.flush_search();index_ms=(time.perf_counter()-start)*1000
 print('indexed '+count+' '+str(round(index_ms,2)),flush=True)
 metrics={'firstUsableMetadataAndPageMs':first_usable,'fallbackChineseMs':fallback_ms,'fallbackTotal':fallback['total'],'indexBuildMs':index_ms,'databaseBytes':store.db.stat().st_size,'data':str(directory)}
 cases={'firstPage':{},'chinese':{'filters':{'search':'动效'}},'singleChinese':{'filters':{'search':'动'}},'english':{'filters':{'search':'React'}},'mixed':{'filters':{'search':'React 动效','tags':['组件'],'collection':'创作'}},'clearSearch':{},'category':{'filters':{'category':'UI / 设计'}},'project':{'filters':{'collection':'创作'}},'codeSymbols':{'filters':{'search':'C++ foo::bar'}}}
 for name,body in cases.items():
  cold_start=time.perf_counter();cold_page=store.query_resources(body);cold_ms=(time.perf_counter()-cold_start)*1000
  metrics[name],page=sample(lambda:store.query_resources(body))
  metrics[name]['firstFilterQueryMs']=cold_ms
  assert page['total']==cold_page['total']
  metrics[name].update(total=page['total'],jsonBytes=len(json.dumps(page,ensure_ascii=False).encode()))
 # Deep offset with a signed revision-bound cursor, not 800 network fetches.
 q=store._with_query(lambda c:store._query_context({},c));rev=store.library_metadata()['revision']
 cursor=store._cursor({'revision':rev,'query':q['fingerprint'],'offset':max(0,info['active']-60)})
 metrics['deepPage'],_=sample(lambda:store.query_resources({'cursor':cursor}))
 metrics['metadata'],_=sample(store.library_metadata)
 metrics['fullState'],_=sample(store.state,5)
 metrics['allMatchIDs'],ids=sample(lambda:store.query_ids({'filters':{'search':'动效'}}),5)
 target=ids['ids'][0];start=time.perf_counter();store.save({'notes':'人工改动 searchincremental'},target);store.query_resources({'filters':{'search':'searchincremental'}});metrics['oneEditAndIndexMs']=(time.perf_counter()-start)*1000
 metrics['processPeakRssBytesIncludingFullExport']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 store.stop_search_worker()
 result['datasets'][count]=metrics
 Path('/tmp/shiji-v62-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'count':count,'firstPage':metrics['firstPage'],'chinese':metrics['chinese'],'fullState':metrics['fullState']},ensure_ascii=False),flush=True)
