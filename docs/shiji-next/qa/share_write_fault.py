"""Reversible metadata-write failure in the independently owned QA App Group.

No product code hooks. Enable while a QA share form is visible, attempt Save,
observe the real error, restore, then retry Save. Always restore before leaving.
"""
import argparse
import hashlib
import json
import stat
import subprocess
from pathlib import Path


def checksums(root):
    return {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(root.rglob('*')) if f.is_file()}


p = argparse.ArgumentParser()
p.add_argument('--device', required=True)
p.add_argument('action', choices=['enable', 'restore'])
a = p.parse_args()
devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json']))
if not any(d['udid'] == a.device and d['name'] == 'Shiji Next Share QA'
           for group in devices['devices'].values() for d in group):
    raise SystemExit('Only the independently owned Next QA simulator is allowed')
container = Path(subprocess.check_output([
    'xcrun', 'simctl', 'get_app_container', a.device,
    'local.silver.shiji.nextqa.app', 'group.local.silver.shiji.nextqa'], text=True).strip())
root = container / 'Library'
assert root.is_dir() and not root.is_symlink()
assert all(not f.is_symlink() for f in root.rglob('*')), 'QA paths must not be symlinks'
marker = container / 'next-share-write-fault.json'
if a.action == 'enable':
    assert json.loads((root / 'library.json').read_text())['schemaVersion'] == 3
    before = dict(device=a.device, mode=stat.S_IMODE(root.stat().st_mode), files=checksums(root))
    assert before['mode'] & 0o200, 'QA store must initially be writable'
    with marker.open('x') as out:
        json.dump(before, out)
    try:
        root.chmod(0o500)  # files remains writable; metadata atomic replace fails.
    except BaseException:
        root.chmod(before['mode'])
        marker.unlink()
        raise
    print('Enabled QA metadata write failure; run restore before leaving this test')
else:
    before = json.loads(marker.read_text())
    assert before['device'] == a.device and isinstance(before['mode'], int)
    root.chmod(before['mode'])  # Restore permissions even if the assertion below fails.
    marker.unlink()
    unchanged = checksums(root) == before['files']
    print(json.dumps(dict(restored=True, metadataAndAttachmentsUnchanged=unchanged)))
    assert unchanged, 'Failed save changed metadata or left a new attachment'
