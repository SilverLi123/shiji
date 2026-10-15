"""Read-only verification of the separately identified V6.1 App Group."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

p = argparse.ArgumentParser()
p.add_argument('--require-safari', action='store_true')
p.add_argument('--snapshot', type=Path)
p.add_argument('--unchanged', type=Path)
a = p.parse_args()
s = json.loads(Path('/tmp/shiji-v61-phone.json').read_text())
assert s['appId']=='local.silver.shiji.v61qa.app' and s['group']=='group.local.silver.shiji.v61qa'
devices = json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json']))
assert any(d['udid']==s['device'] and d['name']=='Shiji Next Share QA' for group in devices['devices'].values() for d in group)
group = Path(subprocess.check_output(['xcrun','simctl','get_app_container',s['device'],s['appId'],s['group']],text=True).strip())
library = group/'Library'
database = library/'library.json'
value = json.loads(database.read_text()) if database.exists() else {'schemaVersion':3,'resources':[]}
assert value['schemaVersion']==3
resources = value['resources']
assert len({r['id'] for r in resources})==len(resources)
if a.require_safari:
    assert any(urlsplit(r.get('url','')).hostname=='example.com' and not r.get('deleted') for r in resources), 'Actual Safari save not present'
for r in resources:
    for attachment in r.get('attachments',[]):
        data = (library/'files'/attachment['id']).read_bytes()
        assert len(data)==attachment['size'] and hashlib.sha256(data).hexdigest()==attachment['sha256']
checks = {str(f.relative_to(library)):hashlib.sha256(f.read_bytes()).hexdigest() for f in library.rglob('*') if f.is_file()}
if a.unchanged:
    assert checks==json.loads(a.unchanged.read_text()), 'Cancellation changed original files'
if a.snapshot:
    with a.snapshot.open('x') as out:
        json.dump(checks,out,indent=2)
print(json.dumps({'schema':3,'resources':len(resources),'records':[{'id':r['id'],'title':r['title'],'url':r.get('url',''),'attachments':len(r.get('attachments',[]))} for r in resources], 'safariVerified':a.require_safari,'cancelUnchanged':bool(a.unchanged)},ensure_ascii=False))
