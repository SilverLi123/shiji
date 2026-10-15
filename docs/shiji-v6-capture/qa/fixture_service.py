"""Real local service + test-only public-host HTTP transport, disposable stores only."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'desktop-app'), str(ROOT/'desktop-app/tests')]
import server
from storage import Store
from capture_fixture import Fixture

p = argparse.ArgumentParser()
p.add_argument('--data-dir', type=Path, required=True)
p.add_argument('--port', type=int, default=0)
a = p.parse_args()
directory = a.data_dir.resolve()
assert directory.is_relative_to(Path(tempfile.gettempdir()).resolve())
assert any(part.startswith('shiji-v6-') for part in directory.parts), 'Only disposable V6 QA stores'
fixture = Fixture()
server.STORE = Store(directory)
http = server.ThreadingHTTPServer(('127.0.0.1', a.port), server.Handler)
with fixture.route(timeout=.15):
    server.STORE.start_capture_worker()
    print(json.dumps({'base': 'http://127.0.0.1:'+str(http.server_port), 'data': str(directory)}), flush=True)
    try:
        http.serve_forever()
    finally:
        server.STORE.stop_capture_worker()
        http.server_close()
        fixture.close()
