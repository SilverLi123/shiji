"""Stream Chrome performance events; never load a large trace into memory as one JSON object."""
import argparse,collections,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
def events(path):
 decoder=json.JSONDecoder()
 with path.open() as f:
  buffer=''
  while True:
   buffer+=f.read(65536);match=re.search(r'"traceEvents"\s*:\s*\[',buffer)
   if match:buffer=buffer[match.end():];break
   if len(buffer)>1048576 or not buffer:raise ValueError('Missing traceEvents')
  pos=0
  while True:
   while pos<len(buffer) and buffer[pos] in ' ,\r\n\t':pos+=1
   if pos<len(buffer) and buffer[pos]==']':return
   try:value,end=decoder.raw_decode(buffer,pos)
   except json.JSONDecodeError:
    more=f.read(1048576)
    if not more:raise
    buffer=buffer[pos:]+more;pos=0;continue
   pos=end;yield value
counts=collections.Counter();durations=collections.Counter();threads={};by_thread=collections.defaultdict(collections.Counter);script=collections.Counter();first=last=None
for e in events(a.trace):
 if e.get('ph')=='M' and e.get('name')=='thread_name':threads[f"{e['pid']}:{e['tid']}"]=e.get('args',{}).get('name')
 if e.get('ph')!='X' or not e.get('dur'):continue
 name=e['name'];duration=e['dur']/1000;counts[name]+=1;durations[name]+=duration;by_thread[f"{e['pid']}:{e['tid']}"][name]+=duration
 first=min(first if first is not None else e['ts'],e['ts']);last=max(last or 0,e['ts']+e['dur'])
 if name=='FunctionCall':
  d=e.get('args',{}).get('data',{});script[(str(d.get('url','')).split('/')[-1]+':'+str(d.get('lineNumber'))+':'+str(d.get('functionName')))]+=duration
result={'source':str(a.trace),'durationMs':(last-first)/1000 if first is not None else None,'note':'Complete-event inclusive durations; nesting and parallel threads overlap. Not exclusive CPU or compositor FPS.','topEvents':durations.most_common(30),'counts':dict(counts),'threads':threads,'byThread':{k:v.most_common(15) for k,v in by_thread.items()},'functionCalls':script.most_common(20)}
a.output.write_text(json.dumps(result,indent=2));print(json.dumps({'durationMs':result['durationMs'],'top':result['topEvents'][:12]}))
