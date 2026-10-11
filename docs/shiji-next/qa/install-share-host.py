"""Build a QA-only UIKit system-share host on the explicitly owned QA simulator.
Never included in Shiji's app targets or production packages.
"""
import argparse,json,plistlib,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--device',required=True);args=p.parse_args()
def run(*cmd,**kw):return subprocess.run([str(x) for x in cmd],check=True,**kw)
devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json']))
assert any(d['udid']==args.device and d['name']=='Shiji Next Share QA' for group in devices['devices'].values() for d in group),'Only the named disposable QA simulator is allowed'
root=Path(tempfile.mkdtemp(prefix='shiji-next-share-host-'));app=root/'ShareQA.app';app.mkdir()
info=dict(CFBundleIdentifier='local.silver.shiji.nextqa.host',CFBundleExecutable='ShareQA',CFBundleName='ShareQA',CFBundleDisplayName='Share QA',CFBundlePackageType='APPL',CFBundleVersion='1',CFBundleShortVersionString='1.0',LSRequiresIPhoneOS=True,UILaunchScreen={},UIDeviceFamily=[1],MinimumOSVersion='17.0',UIApplicationSceneManifest=dict(UIApplicationSupportsMultipleScenes=False))
(app/'Info.plist').write_bytes(plistlib.dumps(info))
sdk=subprocess.check_output(['xcrun','--sdk','iphonesimulator','--show-sdk-path'],text=True).strip()
run('xcrun','--sdk','iphonesimulator','swiftc','-sdk',sdk,'-target','arm64-apple-ios17.0-simulator','-parse-as-library',Path(__file__).with_name('share-host.swift'),'-o',app/'ShareQA')
run('codesign','--force','--sign','-',app);run('xcrun','simctl','install',args.device,app)
print(f'QA host installed at {app}. Launch local.silver.shiji.nextqa.host on the same owned simulator; then use the system sheet to invoke Shiji. No system-share pass is implied by this script.')
