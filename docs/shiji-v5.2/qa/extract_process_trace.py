"""Export only named QA PIDs from a local all-process Instruments table.
The full system recording remains local; unrelated process stacks are not delivered.
"""
import argparse,collections,json,xml.etree.ElementTree as ET,gzip
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('xml',type=Path);p.add_argument('output',type=Path);p.add_argument('--pids',type=int,nargs='+',required=True);p.add_argument('--start',type=float,required=True);p.add_argument('--end',type=float,required=True);a=p.parse_args()
root=ET.parse(a.xml).getroot();ids={e.get('id'):e for e in root.iter() if e.get('id')}
def resolve(e):return ids[e.get('ref')] if e.get('ref') else e
rows=[]
for row in root.iter('row'):
 t=float(resolve(row.find('sample-time')).text)/1e9
 if not a.start<=t<=a.end:continue
 process=resolve(row.find('process'));pid=int(resolve(process.find('pid')).text)
 if pid not in a.pids:continue
 stack=row.find('tagged-backtrace');frames=[resolve(f).get('name','') for f in resolve(stack)] if stack is not None else []
 modules=[resolve(resolve(f).find('binary')).get('name','') if resolve(f).find('binary') is not None else '' for f in resolve(stack)] if stack is not None else []
 rows.append(dict(modules=modules,time=t,ms=float(resolve(row.find('weight')).text)/1e6,pid=pid,thread=resolve(row.find('thread')).get('fmt',''),frames=frames,core=resolve(row.find('core')).get('fmt','')))
with gzip.open(a.output,'wt') as f:json.dump({'window':[a.start,a.end],'pids':a.pids,'samples':rows},f)
summary={}
for pid in a.pids:
 selected=[r for r in rows if r['pid']==pid];leaf=collections.Counter();threads=collections.Counter()
 for r in selected:leaf[r['frames'][0] if r['frames'] else 'empty']+=r['ms'];threads[r['thread']]+=r['ms']
 summary[pid]={'weightMs':sum(r['ms'] for r in selected),'threads':dict(threads),'leaf':leaf.most_common(12)}
print(json.dumps(summary,indent=2))
