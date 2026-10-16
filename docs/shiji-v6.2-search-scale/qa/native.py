"""Build a separately identified QA shell; all source/data/credentials are disposable."""
import argparse,json,sys,tempfile,sqlite3,shutil,socket,plistlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--size',default='1000',choices=['1000','5000','20000','50000']);args=p.parse_args()
before=json.loads(Path('/tmp/shiji-v62-before.json').read_text());root=Path(tempfile.mkdtemp(prefix='shiji-v62-native-'));data=root/'data';data.mkdir()
with sqlite3.connect(Path(before['datasets'][args.size]['data'])/'library.sqlite3') as c,sqlite3.connect(data/'library.sqlite3') as d:c.backup(d)
shutil.copytree(Path(before['datasets'][args.size]['data'])/'files',data/'files')
app=root/f'Shiji V62 QA {args.size}.app';shutil.copytree(ROOT/'desktop-app/dist/Dev Resource Library.app',app)
backend=app/'Contents/Resources/backend';shutil.rmtree(backend);backend.mkdir()
for path in (ROOT/'desktop-app').glob('*.py'):shutil.copy2(path,backend/path.name)
shutil.copytree(ROOT/'desktop-app/static',backend/'static')
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
info=app/'Contents/Info.plist';meta=plistlib.loads(info.read_bytes());meta.update(CFBundleIdentifier='local.silver.shiji.v62.qa'+args.size,CFBundleName='Shiji V62 QA '+args.size,CFBundleDisplayName='Shiji V6.2 QA '+args.size,LSEnvironment={'SHIJI_PORT':str(port),'SHIJI_DATA_DIR':str(data),'SHIJI_PYTHON':sys.executable,'SHIJI_QA_METRICS':'1','SHIJI_SYNC_PORT':'0'});meta.pop('CFBundleURLTypes',None);info.write_bytes(plistlib.dumps(meta))
source=(ROOT/'desktop-app/desktop/App.swift').read_text().replace('func snapshot(_ view: WKWebView, _ event: String) {','func snapshot(_ view: WKWebView, _ event: String) {\n            if view.responds(to:NSSelectorFromString("_webProcessIdentifier")), let pid=view.value(forKey:"_webProcessIdentifier") as? NSNumber { runtime.diagnostics.record("qa.process",["pid":pid.intValue,"host":ProcessInfo.processInfo.processIdentifier]) }\n')
(root/'App.swift').write_text(source)
subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-target','arm64-apple-macosx14.0','-O',str(root/'App.swift'),*[str(p) for p in sorted((ROOT/'desktop-app/desktop').glob('*.swift')) if p.name!='App.swift'],'-o',str(app/'Contents/MacOS/DevResourceLibrary')],check=True)
with (backend/'static/runtime-diagnostics.js').open('a') as f:f.write('\n'+Path(__file__).with_name('probe.js').read_text())
subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
state={'root':str(root),'data':str(data),'app':str(app),'port':port,'size':args.size,'bundle':meta['CFBundleIdentifier']};Path('/tmp/shiji-v62-native-'+args.size+'.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
