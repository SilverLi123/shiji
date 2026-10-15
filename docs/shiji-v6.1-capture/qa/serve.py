"""Disposable V5 backend and independently identified manual-install extension."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'desktop-app'))
import server
from storage import Store

root = Path(tempfile.mkdtemp(prefix='shiji-v61-qa-'))
server.STORE = Store(root/'data')
http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
base = 'http://127.0.0.1:'+str(http.server_port)
extension = root/'extension'
shutil.copytree(ROOT/'desktop-app/browser-extension', extension)
manifest = extension/'manifest.json'
info = json.loads(manifest.read_text())
info['name'] = '拾集 V6.1 QA · 临时资源库'
manifest.write_text(json.dumps(info, ensure_ascii=False, indent=2))
# QA-only bootstrap: no real pairing credentials, and never the formal port.
config = {'base': base, 'token': server.STORE.token()}
(extension/'qa-config.js').write_text('const SHIJI_QA_READY=chrome.storage.local.set('+json.dumps(config)+');\n')
(extension/'qa-config.js').chmod(0o600)
background = extension/'background.js'
source = background.read_text().replace("importScripts('utils.js'", "importScripts('qa-config.js','utils.js'")
source = source.replace('async function configuration(){', 'async function configuration(){await SHIJI_QA_READY;')
source = source.replace("value.base||'http://127.0.0.1:8782'", 'value.base||'+json.dumps(base))
background.write_text(source)
state = {'root': str(root), 'base': base, 'data': str(root/'data'), 'extension': str(extension), 'pid': os.getpid()}
Path('/tmp/shiji-v61-qa.json').write_text(json.dumps(state))
print(json.dumps(state), flush=True)
server.STORE.start_capture_worker()
try:
    http.serve_forever()
finally:
    server.STORE.stop_capture_worker()
    http.server_close()
