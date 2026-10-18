"""Deterministic actual Store datasets, local derived cover preferences, disposable directories only."""
import json
import io
import tarfile
import subprocess
import platform
import shutil
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
root=Path(tempfile.mkdtemp(prefix='shiji-v64-scale-'))
sys.path[:0]=[str(ROOT/'desktop-app'),str(ROOT/'desktop-app/tests')]
from storage import Store,CATEGORIES
from capture_fixture import png_bytes

def measure(fn,repeats=7):
    values=[]
    for _ in range(repeats):
        start=time.perf_counter();fn();values.append((time.perf_counter()-start)*1000)
    ordered=sorted(values)
    return {'samplesMs':values,'p50Ms':statistics.median(values),'p95Ms':ordered[min(len(values)-1,int(len(values)*.95))]}

result={'sourceCommit':'31eeea2','root':str(root),'source':str(ROOT/'desktop-app'),'environment':{'sqlite':sqlite3.sqlite_version,'python':sys.version,'platform':platform.platform()},'datasets':{}}
statefile=Path('/tmp/shiji-v64-fixtures.json')
for count in (1000,5000,20000,50000):
    store=Store(root/str(count));store.capture_action({'action':'pause'})
    store.collection('创作');store.collection('界面','创作');store.collection('研究')
    store.smart({'name':'组件收藏','filters':{'tags':['组件']}})
    start=time.perf_counter()
    with store.lock,store.connect() as c:
        for i in range(count):
            kind=['website','code','prompt','file'][i%4]
            r=store._write(c,{'title':f'{i:05d} '+['动效组件 React Motion','设计灵感 CSS Grid','模型训练 Python API','音频素材 Spatial Studio'][i%4],
                'kind':kind,'url':f'https://example.com/resource/{i}' if kind=='website' else '',
                'category':CATEGORIES[i%len(CATEGORIES)],'tags':['组件' if i%3==0 else '参考','New, exact','React' if i%5==0 else '设计'],
                'projects':['界面'] if i%3==0 else ['研究'] if i%7==0 else [],'projectNotes':{'界面':'按钮交互动效与 C++ foo::bar'} if i%3==0 else {},
                'notes':'本机离线灵感笔记 中文测试 '+('a'*160),'description':'用于真实 Store 的确定性性能样本，覆盖中英文、代码与附件。',
                'snippet':'const useState = (value) => value; // 动效\n'+('print("React")\n'*30) if kind in ('code','prompt') else '',
                'language':'JavaScript' if kind=='code' else '', 'author':'QA Author','sourceUrl':'https://source.example.com/reference',
                'coverConfig':{'style':['editorial','spatial','developer','kinetic','minimal'][i%5],'template':['a','b','c'][i%3],'imageSource':'auto' if i%2 else 'poster'},
                'createdAt':f'2026-10-{1+i%14:02d}T01:00:00Z','favorite':i%5==0,'inbox':i%3==0},apply_auto=False)
            if i%20==0:
                store.attach_in_transaction(c,r['id'],png_bytes(),{'name':f'布局参考-{i}.png','cover':True,'sourceUrl':'https://assets.example.com/image','author':'Image QA'},[])
            if i%17==0:c.execute('UPDATE resources SET deleted=1 WHERE id=?',(r['id'],))
    seeded=time.perf_counter()-start
    print(f'seeded {count} in {seeded:.3f}s; measuring full state',flush=True)
    cold_start=time.perf_counter();data=store.state();cold_ms=(time.perf_counter()-cold_start)*1000
    warm=measure(store.state,5)
    datafile=root/f'{count}-resources.json';datafile.write_text(json.dumps(data,ensure_ascii=False))
    info={'data':str(store.root),'fullStateColdMs':cold_ms,'fullStateWarm':warm,'seedSeconds':seeded,
          'jsonBytes':datafile.stat().st_size,'active':len(data['resources']),'total':count,'attachments':count//20}
    result['datasets'][str(count)]=info
    statefile.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'count':count,**info},ensure_ascii=False),flush=True)
    store.stop_search_worker()
print('Baseline source and raw samples retained at '+str(root),flush=True)
