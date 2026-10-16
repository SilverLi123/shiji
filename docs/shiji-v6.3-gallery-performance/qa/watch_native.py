"""Read QA-only native journal and sample its identified processes during idle scenes."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('output');a=p.parse_args()
state=json.loads(Path(a.manifest).read_text());data=Path(state['data']);output=Path(a.output);output.parent.mkdir(exist_ok=True)
seen=set();samplers=[];deadline=time.monotonic()+2400;started=time.time();last=None
while time.monotonic()<deadline:
 rows=[]
 for f in [data/'runtime-events.jsonl.previous',data/'runtime-events.jsonl']:
  if not f.exists():continue
  for line in f.read_text().splitlines():
   try:rows.append(json.loads(line))
   except ValueError:pass
 rows.sort(key=lambda r:r.get('time',0))
 process=next((r for r in reversed(rows) if r.get('event')=='qa.process'),None)
 backend=next((r.get('pid') for r in reversed(rows) if r.get('event')=='service.spawn'),None)
 row=next((r for r in reversed(rows) if r.get('event')=='qa.v63-scenario' and r.get('time',0)>started-2),None)
 if row:
  journal=json.loads(row['phase']);output.write_text(json.dumps({'manifest':state,'process':process,'backend':backend,'journal':journal},indent=2)+'\n');last=journal
  step=journal.get('runningStep',{}).get('name','')
  if step.endswith('idle30') and step not in seen and process and backend:
   seen.add(step);file=output.with_name(output.stem+'-'+step+'-process.jsonl');handle=file.open('w')
   sampler=subprocess.Popen(['/tmp/shiji-v63-process-sample','30',str(process['host']),str(process['pid']),str(backend)],stdout=handle)
   samplers.append((sampler,handle));print('sampling',step,process['host'],process['pid'],backend,flush=True)
  if journal.get('completed') or journal.get('error'):break
 time.sleep(.2)
for process,handle in samplers:process.wait();handle.close()
if not last or not last.get('completed'):raise SystemExit('Native scene incomplete: '+str(last and last.get('error')))
print('completed',len(last['steps']),'native scene measurements',flush=True)
