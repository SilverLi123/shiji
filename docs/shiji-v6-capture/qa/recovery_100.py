"""100 real API URL saves, SIGKILL/restart, actual lease expiry and cover checks.

Keep test databases and service logs in a temporary directory, never production/Git.
"""
import base64
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'desktop-app/tests'))
from capture_fixture import png_bytes


def request(base, path, body=None, headers=None):
    headers = dict(headers or {})
    if isinstance(body, dict):
        body = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    with urlopen(Request(base+path, body, headers), timeout=5) as response:
        return json.load(response)


directory = Path(tempfile.mkdtemp(prefix='shiji-v6-recovery-100-'))
data = directory/'data'
processes = []


def launch(attempt):
    log = (directory/f'service-{attempt}.log').open('w')
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('fixture_service.py')), '--data-dir', str(data)], stdout=subprocess.PIPE, stderr=log, text=True)
    processes.append(process)
    line = process.stdout.readline()
    assert line, 'Fixture service failed to start: '+str(directory)
    return process, json.loads(line)['base']


started = time.monotonic()
try:
    process, base = launch(1)
    request(base, '/api/capture/tasks', {'action': 'pause'})
    resources = []
    kinds = ('page', 'incomplete', 'bad-cover', 'redirect-private', 'fail', 'slow', 'redirect', 'page', 'page', 'page')
    for i in range(100):
        host = 'offline.fixture.invalid' if i % 10 == 8 else 'capture.fixture.invalid'
        path = ('slow' if i == 0 else kinds[i % 10])+'/'+str(i)
        resources.append(request(base, '/api/resources', {'url': 'http://'+host+'/'+path, 'title': host, 'quickCapture': True})['resource'])
    assert len(request(base, '/api/resources')['resources']) == 100
    # Repeat real quick captures rather than generating an independent task model.
    for r in resources[:15]:
        result = request(base, '/api/resources', {'url': r['url'], 'title': 'Incoming title', 'quickCapture': True})
        assert result['resource']['id'] == r['id']
    request(base, '/api/resources/'+resources[7]['id']+'/edit', {'changes': {'title': '手动标题保持不变'}, 'expected': {'title': resources[7]['title']}})
    request(base, '/api/resources/'+resources[17]['id']+'/edit', {'changes': {'category': '音频', 'tags': ['New, exact']}, 'expected': {'category': resources[17]['category'], 'tags': []}})
    header = base64.b64encode(json.dumps({'name': 'Manual cover', 'cover': True}).encode()).decode()
    request(base, '/api/resources/'+resources[27]['id']+'/attachments', png_bytes(), {'Content-Type': 'application/octet-stream', 'X-Metadata': header})
    manual_cover = request(base, '/api/resources/'+resources[27]['id'])['resource']['coverId']
    request(base, '/api/capture/tasks', {'action': 'resume'})
    deadline = time.monotonic()+15
    while True:
        with sqlite3.connect(data/'library.sqlite3') as c:
            active = c.execute("SELECT id FROM capture_jobs WHERE resource_id=? AND status='running'", (resources[0]['id'],)).fetchone()
        if active:
            request(base, '/api/resources/'+resources[0]['id']+'/edit', {'changes': {'title': '运行期间编辑保持不变'}, 'expected': {'title': resources[0]['title']}})
            break
        assert time.monotonic() < deadline, 'Did not observe first real running task'
        time.sleep(.01)
    print('100 durable resources; repeated captures deduplicated; manual edits applied', flush=True)
    deadline = time.monotonic()+90
    while True:
        with sqlite3.connect(data/'library.sqlite3') as c:
            terminal = c.execute("SELECT count(*) FROM capture_jobs WHERE status NOT IN ('pending','running','retry')").fetchone()[0]
            active = c.execute("SELECT id,lease_until FROM capture_jobs WHERE status='running' AND url LIKE '%/slow/%' ORDER BY created_at LIMIT 1").fetchone()
        if terminal >= 15 and active:
            process.kill()  # genuine abrupt death, not a graceful shutdown fixture.
            process.wait(timeout=5)
            break
        assert time.monotonic() < deadline, 'No observable mid-run lease for SIGKILL'
        time.sleep(.01)
    with sqlite3.connect(data/'library.sqlite3') as c:
        killed = c.execute('SELECT status,lease,lease_until FROM capture_jobs WHERE id=?', (active[0],)).fetchone()
        assert killed[0] == 'running' and killed[1], 'Kill must leave an actual running lease'
        assert c.execute('SELECT count(*) FROM resources').fetchone()[0] == 100
    restart_at = time.monotonic()
    process, base = launch(2)
    print('SIGKILL left a durable running lease; restart uses real expiry, no shortened lease', flush=True)
    deadline = time.monotonic()+240
    while True:
        status = request(base, '/api/capture/tasks')
        if status['active'] == 0:
            break
        assert time.monotonic() < deadline, 'Recovery did not converge; artifacts: '+str(directory)
        time.sleep(.25)
    actual = request(base, '/api/resources')['resources']
    byid = {r['id']: r for r in actual}
    assert len(actual) == 100 and len(byid) == 100
    assert byid[resources[7]['id']]['title'] == '手动标题保持不变'
    assert byid[resources[17]['id']]['category'] == '音频'
    assert byid[resources[17]['id']]['tags'] == ['New, exact']
    assert byid[resources[0]['id']]['title'] == '运行期间编辑保持不变'
    assert byid[resources[27]['id']]['coverId'] == manual_cover
    digest = hashlib.sha256(png_bytes()).hexdigest()
    referenced = set()
    for r in actual:
        for a in r['attachments']:
            assert a['resourceId'] == r['id'] and a['sha256'] == digest
            assert (data/'files'/a['id']).read_bytes() == png_bytes()
            referenced.add(a['id'])
        if r['coverId']:
            assert r['coverId'] in {a['id'] for a in r['attachments']}
        assert len(r['attachments']) <= 1, 'Repeated attempts must not duplicate image bytes'
    assert {p.name for p in (data/'files').iterdir()} == referenced
    with sqlite3.connect(data/'library.sqlite3') as c:
        tasks = c.execute('SELECT count(*) FROM capture_jobs').fetchone()[0]
        assert tasks == 100 and c.execute('PRAGMA user_version').fetchone()[0] == 3
        assert c.execute("SELECT count(*) FROM capture_jobs WHERE lease!='' OR status='running'").fetchone()[0] == 0
    assert status['counts']['skipped'] == 4
    assert status['counts']['failed'] == 50
    assert status['counts']['completed'] == 46
    result = {'result': 'PASS', 'urls': 100, 'resources': len(actual), 'tasks': tasks,
              'states': status['counts'], 'attachments': len(referenced),
              'elapsedSeconds': round(time.monotonic()-started, 3),
              'restartToCompletionSeconds': round(time.monotonic()-restart_at, 3),
              'leaseSeconds': 120, 'fixtureNetworkTimeoutSeconds': .15,
              'killedTask': active[0], 'artifactDirectory': str(directory),
              'limitations': ['Test-only public-host transport uses a local HTTP fixture', 'Shorter network deadlines exercise timeouts; production lease/backoff unchanged', 'This is backend/API acceptance, not physical iPhone or macOS UI acceptance']}
    (directory/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False), flush=True)
finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
