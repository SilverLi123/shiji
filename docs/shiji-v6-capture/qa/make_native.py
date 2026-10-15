"""Normal product native runtime with forced disposable data/port and unique identity.

No delayed reloads, synthetic clicks or animation changes. Original App.swift
and the product bundle remain unchanged; only this temporary copy is compiled.
"""
import argparse
import json
import plistlib
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument('--count', type=int, choices=[1000, 5000], default=1000)
a = p.parse_args()
bench = json.loads(Path('/tmp/shiji-v6-performance.json').read_text())
source = Path(bench['datasets'][str(a.count)]['state']).resolve()
assert source.is_relative_to(Path(tempfile.gettempdir()).resolve()) and source.parent.name.startswith('shiji-v6-performance-')
root = Path(tempfile.mkdtemp(prefix='shiji-v6-native-'))
data = root/'data'
data.mkdir()
import sqlite3
with sqlite3.connect(source/'library.sqlite3') as c, sqlite3.connect(data/'library.sqlite3') as d:
    c.backup(d)
shutil.copytree(source/'files', data/'files')
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
app = root/f'Shiji V6 Capture QA {a.count}.app'
shutil.copytree(ROOT/'desktop-app/dist/Dev Resource Library.app', app)
backend = app/'Contents/Resources/backend'
for module in (ROOT/'desktop-app').glob('*.py'):
    shutil.copy2(module, backend/module.name)
shutil.copytree(ROOT/'desktop-app/static', backend/'static', dirs_exist_ok=True)
info = app/'Contents/Info.plist'
metadata = plistlib.loads(info.read_bytes())
metadata.update(CFBundleIdentifier=f'local.silver.shiji.v6-capture-qa-{a.count}', CFBundleDisplayName=f'拾集 V6 Capture QA {a.count}', CFBundleName=f'Shiji V6 Capture QA {a.count}')
metadata.pop('CFBundleURLTypes', None)
info.write_bytes(plistlib.dumps(metadata))
swift = (ROOT/'desktop-app/desktop/App.swift').read_text()
start = swift.index('    var dataDirectory: URL {')
end = swift.index('    lazy var diagnostics', start)
swift = swift[:start]+'    var dataDirectory: URL { URL(fileURLWithPath: '+json.dumps(str(data))+') }\n'+swift[end:]
swift = swift.replace('let port = Int(ProcessInfo.processInfo.environment["SHIJI_PORT"] ?? "8782") ?? 8782', f'let port = {port}')
swift = swift.replace('let candidates = [ProcessInfo.processInfo.environment["SHIJI_PYTHON"], "/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3"].compactMap { $0 }', 'let candidates = ['+json.dumps(sys.executable)+']')
swift = swift.replace('environment["PYTHONUNBUFFERED"] = "1"', 'environment["PYTHONUNBUFFERED"] = "1"; environment["SHIJI_SYNC_PORT"] = "0"')
assert 'appendingPathComponent("DevResourceLibrary")' not in swift
qa = root/'App.swift'
qa.write_text(swift)
subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '5', '-target', 'arm64-apple-macosx14.0', '-O', str(qa), *[str(p) for p in sorted((ROOT/'desktop-app/desktop').glob('*.swift')) if p.name != 'App.swift'], '-o', str(app/'Contents/MacOS/DevResourceLibrary')], check=True)
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
state = {'root': str(root), 'app': str(app), 'data': str(data), 'port': port, 'count': a.count, 'bundle': metadata['CFBundleIdentifier']}
Path(f'/tmp/shiji-v6-native-{a.count}.json').write_text(json.dumps(state))
print(json.dumps(state))
