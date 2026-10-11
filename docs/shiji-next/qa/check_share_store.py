"""Read-only assertions for actual system-share output in the owned QA simulator.

This does not invoke the extension and cannot certify system UI or physical devices.
Run after actual UI saves; never point this at a production directory.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--device', required=True)
p.add_argument('--snapshot', type=Path, help='Write checksums to a new QA evidence file')
p.add_argument('--unchanged', type=Path, help='Compare with a prior cancellation snapshot')
p.add_argument('--safari-saved', action='store_true', help='Require the actual Safari share and manual title')
a = p.parse_args()
devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json']))
if not any(d['udid'] == a.device and d['name'] == 'Shiji Next Share QA'
           for group in devices['devices'].values() for d in group):
    raise SystemExit('Only the independently owned Next QA simulator is allowed')
container = Path(subprocess.check_output([
    'xcrun', 'simctl', 'get_app_container', a.device,
    'local.silver.shiji.nextqa.app', 'group.local.silver.shiji.nextqa'], text=True).strip())
store = container / 'Library'
data = json.loads((store / 'library.json').read_text())
assert data['schemaVersion'] == 3
resources = data['resources']
assert len({r['id'] for r in resources}) == len(resources)
url = next(r for r in resources if r['url'] == 'https://example.com/shiji-next-share-qa')
text = next(r for r in resources if r['notes'] == 'SHIJI Next QA — actual system text share, New, exact')
assert text['title'] == '20261011', 'Actual manually entered title must be preserved'
if a.safari_saved:
    safari = next(r for r in resources if r['url'] == 'https://example.com/?shiji-next-safari=1')
    assert safari['title'] == '55102026', 'Safari manual title must survive saving'
image = next(r for r in resources if r['attachments'])
assert image['coverId'] == image['attachments'][0]['id']
for r in resources:
    for attachment in r['attachments']:
        file = store / 'files' / attachment['id']
        payload = file.read_bytes()
        assert len(payload) == attachment['size']
        assert hashlib.sha256(payload).hexdigest() == attachment['sha256']
        assert attachment['mime'] == 'image/jpeg' and payload.startswith(b'\xff\xd8\xff')
checksums = {str(file.relative_to(store)): hashlib.sha256(file.read_bytes()).hexdigest()
             for file in sorted(store.rglob('*')) if file.is_file()}
if a.unchanged:
    assert checksums == json.loads(a.unchanged.read_text()), 'Cancel must leave metadata and attachments unchanged'
if a.snapshot:
    with a.snapshot.open('x') as out:
        json.dump(checksums, out, indent=2)
print(json.dumps({'schema': 3, 'resources': len(resources), 'actualURL': url['url'],
                  'manualTextTitle': text['title'], 'imageAttachmentsVerified': len(image['attachments']),
                  'cancelUnchanged': bool(a.unchanged), 'safariSaveVerified': a.safari_saved}, ensure_ascii=False))
