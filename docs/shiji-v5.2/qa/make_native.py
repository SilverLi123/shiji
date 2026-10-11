"""Reuse V5.1 temporary fixture/bundle generation, replace intrusive probe only."""
import argparse,json,subprocess,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=1000);p.add_argument('--tag',default='v52baseline');args=p.parse_args()
subprocess.run([sys.executable,str(REPO/'docs/shiji-v5.1/qa/make_native.py'),'--count',str(args.count),'--tag',args.tag],check=True)
state=json.loads(Path(f'/tmp/shiji-v5-stable-{args.tag}-{args.count}.json').read_text());app=Path(state['app']);backend=app/'Contents/Resources/backend/static'
(backend/'runtime-diagnostics.js').write_text(Path(__file__).with_name('probe.js').read_text())
# Replace the QA-only native profile button with one controlled test run.
qaSource=Path(state['root'])/'App.swift'
source=qaSource.read_text().replace('runtime.webView?.evaluateJavaScript("window.ShijiQAProfile?.()")', 'Task { try? await Task.sleep(nanoseconds:2_000_000_000); NSApp.activate(ignoringOtherApps:true); runtime.webView?.window?.makeKeyAndOrderFront(nil); runtime.webView?.evaluateJavaScript("window.ShijiQARun?.()",completionHandler:nil) }')
qaSource.write_text(source)
subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-target','arm64-apple-macosx14.0','-O',str(qaSource),*[str(p) for p in sorted((REPO/'desktop-app/desktop').glob('*.swift')) if p.name!='App.swift'],'-o',str(app/'Contents/MacOS/DevResourceLibrary')],check=True)
# Original product App.swift is unchanged; original QA maker adds only native process ID/profile UI.
(backend/'app.js').write_text((REPO/'desktop-app/static/app.js').read_text()+'\nconst qaDetailOriginal=detail;detail=function(...args){window.ShijiQATrace.begin();try{return qaDetailOriginal(...args);}finally{window.ShijiQATrace.end();}};')
# Diagnostics are emitted after measured frames. Keep the prior 30s profile button available.
with (backend/'runtime-diagnostics.js').open('a') as f:f.write('\n'+'window.ShijiQAProfile='+(REPO/'docs/shiji-v5.1/qa/trace.js').read_text().split('window.ShijiQAProfile=',1)[1])
subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
print(json.dumps(state))
