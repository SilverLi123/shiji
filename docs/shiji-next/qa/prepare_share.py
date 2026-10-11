"""Copy current mobile sources to a disposable, independently identified QA build."""
import argparse
import json
import plistlib
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument('--device', required=True)
a = p.parse_args()
devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json']))
assert any(d['udid'] == a.device and d['name'] == 'Shiji Next Share QA'
           for group in devices['devices'].values() for d in group), 'Only owned Next QA simulator'
root = Path(tempfile.mkdtemp(prefix='shiji-next-share-'))
mobile = root / 'mobile-app'
mobile.mkdir()
for name in ('App', 'ShareExtension', 'Shared', 'Shiji.xcodeproj'):
    shutil.copytree(REPO / 'mobile-app' / name, mobile / name)
project = mobile / 'Shiji.xcodeproj/project.pbxproj'
s = project.read_text().replace('local.silver.shiji.mobile.share', 'local.silver.shiji.nextqa.app.share')
s = s.replace('local.silver.shiji.mobile', 'local.silver.shiji.nextqa.app')
s = s.replace('group.local.silver.shiji', 'group.local.silver.shiji.nextqa')
project.write_text(s)
for name in ('App', 'ShareExtension'):
    info = mobile / name / 'Info.plist'
    data = plistlib.loads(info.read_bytes())
    data['CFBundleDisplayName'] = '拾集 Next QA'
    info.write_bytes(plistlib.dumps(data))
state = dict(root=str(root), project=str(mobile / 'Shiji.xcodeproj'), device=a.device,
             appId='local.silver.shiji.nextqa.app', group='group.local.silver.shiji.nextqa',
             app=str(root / 'DerivedData/Build/Products/Debug-iphonesimulator/Shiji.app'))
Path('/tmp/shiji-next-share.json').write_text(json.dumps(state))
print(json.dumps(state))
