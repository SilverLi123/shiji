"""Build inputs only: fresh app/group identity on the existing owned QA simulator."""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json']))
device = next(d for group in devices['devices'].values() for d in group if d['name']=='Shiji Next Share QA' and d['state']=='Booted')
root = Path(tempfile.mkdtemp(prefix='shiji-v61-phone-'))
mobile = root/'mobile-app'
mobile.mkdir()
for name in ('App', 'Shared', 'ShareExtension', 'Shiji.xcodeproj'):
    shutil.copytree(ROOT/'mobile-app'/name, mobile/name)
for file in mobile.rglob('*'):
    if file.suffix in ('.plist', '.entitlements', '.pbxproj'):
        value = file.read_text().replace('local.silver.shiji.mobile', 'local.silver.shiji.v61qa.app').replace('group.local.silver.shiji', 'group.local.silver.shiji.v61qa')
        file.write_text(value)
for name in ('App', 'ShareExtension'):
    file = mobile/name/'Info.plist'
    info = plistlib.loads(file.read_bytes())
    info['CFBundleDisplayName'] = '拾集 V6.1 QA'
    file.write_bytes(plistlib.dumps(info))
state = {'root': str(root), 'project': str(mobile/'Shiji.xcodeproj'), 'device': device['udid'],
         'appId': 'local.silver.shiji.v61qa.app', 'group': 'group.local.silver.shiji.v61qa',
         'app': str(root/'DerivedData/Build/Products/Debug-iphonesimulator/Shiji.app')}
Path('/tmp/shiji-v61-phone.json').write_text(json.dumps(state))
print(json.dumps(state))
