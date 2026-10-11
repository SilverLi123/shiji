"""Inclusive per-sample stack weights; categories overlap and MUST NOT be summed."""
import argparse,collections,json,xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('xml',type=Path);p.add_argument('output',type=Path);p.add_argument('--start',type=float,required=True);p.add_argument('--end',type=float,required=True);a=p.parse_args()
root=ET.parse(a.xml).getroot();ids={e.get('id'):e for e in root.iter() if e.get('id')}
def resolve(e):return ids[e.get('ref')] if e.get('ref') else e
patterns={'style':['resolveStyle','Style::Resolver','resolveComputedStyle'],'layout':['updateLayout','::layout(','getBoundingClientRect'],'composite':['buildTransaction','Composit','updateLayer'],'paint':['::paint','DisplayList','BackingStore'],'image':['ImageDecoder','decode','ImageFrame'],'accessibility':['Accessibility','AXCopy','CopyHierarchy'],'ipcWait':['waitFor','sendSync','Connection::wait','semaphore_wait'],'script':['callEventListener','executeJavaScript','evaluateJavaScript','EventTarget::dispatch']}
categories=collections.Counter();leaf=collections.Counter();threads=collections.Counter();buckets={};samples=0
for row in root.iter('row'):
 t=float(resolve(row.find('sample-time')).text)/1e9
 if not a.start<=t<=a.end:continue
 weight=float(resolve(row.find('weight')).text)/1e6
 stack=row.find('tagged-backtrace');frames=[resolve(f).get('name','') for f in resolve(stack)] if stack is not None else []
 thread=resolve(row.find('thread')).get('fmt','');threads[thread]+=weight
 samples+=1;leaf[frames[0] if frames else 'empty']+=weight
 text='\n'.join(frames)
 bucket=round(int(t*10)/10,1);hit=buckets.setdefault(bucket,collections.Counter());hit['total']+=weight
 for name,patterns_ in patterns.items():
  if any(s in text for s in patterns_):categories[name]+=weight;hit[name]+=weight
result={'window':[a.start,a.end],'samples':samples,'inclusiveMs':dict(categories),'threadMs':dict(threads),'leafTop':leaf.most_common(25),'buckets':{str(k):dict(v) for k,v in buckets.items()},'note':'Sampling weights are inclusive and overlapping, not wall-time phase durations.'}
a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
