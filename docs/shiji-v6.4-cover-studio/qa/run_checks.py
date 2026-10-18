"""Full isolated regression/build gates. Reports actual exits, preserves failed attempt logs."""
import json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'desktop-app/dist/v64-full-tests.json'
commands=[('python-portable',['python3','desktop-app/tests/run-ci.py','--suite','portable']),('node',['npm','--prefix','desktop-app','test']),('python-native',['python3','desktop-app/tests/run-ci.py','--suite','native']),('swift',['python3','mobile-app/Tests/run.py']),('https',['python3','mobile-app/Tests/sync_integration.py']),('macos',['python3','desktop-app/desktop/build.py']),('gallery',['python3','desktop-app/tests/run_gallery_browser.py']),('editor',['python3','desktop-app/tests/run_cover_browser.py'])]
rows=json.loads(out.read_text()) if out.exists() else []
for name,cmd in commands:
 old=next((r for r in rows if r['name']==name),None)
 if old and old['exit']==0:continue
 attempt=len(old.get('priorAttempts',[]))+2 if old else 1;log=Path('/tmp')/f'shiji-v64-final-{name}-attempt{attempt}.log';start=time.monotonic();print('START',name,flush=True)
 with log.open('w') as f:r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=f)
 row={'name':name,'command':cmd,'exit':r.returncode,'seconds':time.monotonic()-start,'log':str(log)}
 if old:row['priorAttempts']=old.get('priorAttempts',[])+[{k:v for k,v in old.items() if k!='priorAttempts'}];rows[rows.index(old)]=row
 else:rows.append(row)
 out.write_text(json.dumps(rows,indent=2));print(row,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
