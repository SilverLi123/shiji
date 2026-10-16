"""Sequential fresh-profile browser performance matrix. Only ephemeral QA services."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['before','after'],required=True);p.add_argument('--wait-pid',type=int);a=p.parse_args()
qa=Path(__file__).resolve().parent;repo=qa.parents[2];out=repo/'desktop-app/dist';out.mkdir(exist_ok=True)
if a.wait_pid:
 while True:
  try:os.kill(a.wait_pid,0)
  except ProcessLookupError:break
  time.sleep(1)
for size in [1000,5000,20000,50000]:
 state=Path(f'/tmp/shiji-v63-{a.phase}-{size}.json');state.unlink(missing_ok=True)
 with open(f'/tmp/shiji-v63-matrix-{a.phase}-{size}-server.log','w') as log:
  server=subprocess.Popen([sys.executable,str(qa/'serve.py'),'--size',str(size)]+(['--before'] if a.phase=='before' else []),stdout=log,stderr=log)
  try:
   deadline=time.monotonic()+120
   while not state.exists():
    if server.poll() is not None or time.monotonic()>deadline:raise RuntimeError('QA server failed')
    time.sleep(.1)
   url=json.loads(state.read_text())['url']
   for mode in ['studio','calm']:
    prefix=out/f'v63-{a.phase}-{size}';result=Path(str(prefix)+'-'+mode+'.json')
    if result.exists() and len(json.loads(result.read_text())['rounds'])==3 and all(r.get('completed') for r in json.loads(result.read_text())['rounds']):continue
    with open(f'/tmp/shiji-v63-{a.phase}-{size}-{mode}.log','w') as metrics:
     print(a.phase,size,mode,flush=True)
     subprocess.run(['node',str(qa/'measure-browser.cjs'),url,str(prefix),'3',mode,'2000'],stdout=metrics,stderr=metrics,check=True,timeout=2400)
  finally:
   server.terminate()
   try:server.wait(timeout=10)
   except subprocess.TimeoutExpired:server.kill();server.wait()
