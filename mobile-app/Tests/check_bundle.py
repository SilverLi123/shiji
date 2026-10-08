"""Verify compiled appearance assets and App/share App Group agreement."""
import subprocess,json,plistlib,sys,struct
from pathlib import Path
app=Path(sys.argv[1])
def simulated_entitlements(executable):
 # Xcode embeds simulator entitlements in Mach-O, distinct from signing entitlements.
 data=executable.read_bytes()
 assert struct.unpack_from('<I',data)[0]==0xfeedfacf, 'Expected arm64 thin simulator executable'
 offset=32
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  cmd,size=struct.unpack_from('<II',data,offset)
  if cmd==0x19:
   count=struct.unpack_from('<I',data,offset+64)[0]
   for n in range(count):
    section=offset+72+n*80
    if data[section:section+16].rstrip(b'\0')==b'__entitlements':
     length,start=struct.unpack_from('<QI',data,section+40)
     return plistlib.loads(data[start:start+length])
  offset+=size
 raise AssertionError('Missing simulator entitlements')
for bundle in [app,app/'PlugIns/ShijiShare.appex']:
 info=plistlib.loads((bundle/'Info.plist').read_bytes())
 if 'iPhoneSimulator' in info.get('CFBundleSupportedPlatforms',[]):
  entitlements=simulated_entitlements(bundle/info['CFBundleExecutable'])
 else:
  entitlements=plistlib.loads(subprocess.check_output(['codesign','-d','--entitlements',':-',str(bundle)],stderr=subprocess.DEVNULL))
 assert entitlements['com.apple.security.application-groups']==[info['ShijiAppGroup']]
colors=json.loads(subprocess.check_output(['xcrun','assetutil','--info',str(app/'Assets.car')]))
accents=[x for x in colors if x.get('Name')=='AccentColor' and x.get('AssetType')=='Color']
assert len(accents)==2 and all(x['Color components'][-1]==1 for x in accents)
assert any(x.get('Name','').startswith('AppIcon') for x in colors)
print('PASS: app/share matching App Groups; opaque light/dark accent assets; compiled AppIcon')
