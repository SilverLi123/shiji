#!/usr/bin/env python3
"""Build an ad-hoc signed local macOS .app and unpacked MV3 extension package."""
import plistlib,shutil,subprocess,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
out=root/'dist';out.mkdir(exist_ok=True)
app=out/'Dev Resource Library.app';contents=app/'Contents';mac=contents/'MacOS';resources=contents/'Resources'
mac.mkdir(parents=True,exist_ok=True);resources.mkdir(exist_ok=True)
subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-target','arm64-apple-macosx14.0','-O',*[str(p) for p in sorted((root/'desktop').glob('*.swift'))],'-o',str(mac/'DevResourceLibrary')],check=True)
backend=resources/'backend'
if backend.exists():shutil.rmtree(backend)
backend.mkdir()
for source in root.glob('*.py'):shutil.copy2(source,backend/source.name)
shutil.copytree(root/'static',backend/'static',dirs_exist_ok=True)
extension=resources/'browser-extension';shutil.copytree(root/'browser-extension',extension,dirs_exist_ok=True)
info={'CFBundleName':'Dev Resource Library','CFBundleDisplayName':'拾集','CFBundleIdentifier':'local.silver.dev-resource-library','CFBundleExecutable':'DevResourceLibrary','CFBundlePackageType':'APPL','CFBundleShortVersionString':'1.1.0','CFBundleVersion':'2','LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,'NSLocalNetworkUsageDescription':'在同一 Wi-Fi 与已配对的 iPhone 同步收藏和素材。','NSAppTransportSecurity':{'NSAllowsLocalNetworking':True},'CFBundleURLTypes':[{'CFBundleURLName':'DevResourceLibrary','CFBundleURLSchemes':['shiji']}],'NSAppleEventsUsageDescription':'打开资源库窗口。'}
(contents/'Info.plist').write_bytes(plistlib.dumps(info))
with zipfile.ZipFile(out/'shiji-browser-extension.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in sorted((root/'browser-extension').rglob('*')):
  if path.is_file():archive.write(path,path.relative_to(root/'browser-extension'))
shutil.copy2(out/'shiji-browser-extension.zip',root/'static/browser-extension.zip')
shutil.copy2(out/'shiji-browser-extension.zip',backend/'static/browser-extension.zip')
subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
with zipfile.ZipFile(out/'DevResourceLibrary-macOS-arm64.zip','w',zipfile.ZIP_DEFLATED) as archive:
 archive.write(root/'APP.md','Install Guide.md')
 if (root/'SYNC.md').is_file():archive.write(root/'SYNC.md','SYNC.md')
 for path in sorted(app.rglob('*')):
  if path.is_file():archive.write(path,path.relative_to(out))
print(app)
