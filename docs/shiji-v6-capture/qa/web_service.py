"""Run real V5 UI/API with copied static assets and passive QA timing only."""
import argparse
import json
import shutil
import sys
import tempfile
import os
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'desktop-app'), str(ROOT/'desktop-app/tests')]
import server
from storage import Store
from capture_fixture import Fixture

p = argparse.ArgumentParser()
p.add_argument('--count', type=int, choices=[0, 1000, 5000], default=0)
p.add_argument('--data-dir', type=Path)
p.add_argument('--port', type=int, default=0)
a = p.parse_args()
root = Path(tempfile.mkdtemp(prefix='shiji-v6-web-'))
static = root/'static'
shutil.copytree(ROOT/'desktop-app/static', static)
shutil.copy2(Path(__file__).with_name('observer.js'), static/'qa-observer.js')
index = static/'index.html'
index.write_text(index.read_text().replace('<script src="app.js" defer>', '<script src="qa-observer.js" defer></script><script src="app.js" defer>'))
if a.data_dir:
    data = a.data_dir.resolve()
    assert data.is_relative_to(Path(tempfile.gettempdir()).resolve()) and any(p.startswith('shiji-v6-') for p in data.parts)
elif a.count:
    bench = json.loads(Path('/tmp/shiji-v6-performance.json').read_text())
    data = Path(bench['datasets'][str(a.count)]['state']).resolve()
    assert data.is_relative_to(Path(tempfile.gettempdir()).resolve()) and data.parent.name.startswith('shiji-v6-performance-')
else:
    data = root/'data'
class Handler(server.Handler):
    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, directory=str(static), **kwargs)
    def log_message(self, *args):
        pass
server.STORE = Store(data)
http = server.ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
state = {'root': str(root), 'data': str(data), 'base': 'http://127.0.0.1:'+str(http.server_port), 'count': a.count, 'pid': os.getpid()}
Path(f'/tmp/shiji-v6-web-{a.count}.json').write_text(json.dumps(state))
print(json.dumps(state), flush=True)
fixture = Fixture()
with fixture.route():
    server.STORE.start_capture_worker()
    try:
        http.serve_forever()
    finally:
        server.STORE.stop_capture_worker()
        http.server_close()
        fixture.close()
