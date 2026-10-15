"""Measure real Store query/claim/commit cost with disposable 1000/5000 stores."""
import json
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'desktop-app'), str(ROOT/'desktop-app/tests')]
from storage import Store, CATEGORIES
from capture_fixture import Fixture


def measure(operation, count=25):
    values = []
    for _ in range(count):
        start = time.perf_counter()
        operation()
        values.append((time.perf_counter()-start)*1000)
    ordered = sorted(values)
    return {'samples': values, 'p50ms': round(statistics.median(values), 3),
            'p95ms': round(ordered[min(len(ordered)-1, int(len(ordered)*.95))], 3), 'maxMs': round(max(values), 3)}


directory = Path(tempfile.mkdtemp(prefix='shiji-v6-performance-'))
result = {'environment': {'python': sys.version, 'sqlite': sqlite3.sqlite_version, 'platform': platform.platform()}, 'datasets': {}, 'artifacts': str(directory)}
fixture = Fixture()
try:
    for count in (1000, 5000):
        store = Store(directory/str(count))
        store.capture_action({'action': 'pause'})
        started = time.perf_counter()
        for i in range(count):
            store.save({'title': f'QA {i:05d} · '+['开发资源与工具', '界面排版与组件', '长期灵感笔记'][i%3],
                        'url': 'http://capture.fixture.invalid/page/'+str(i), 'category': CATEGORIES[i%len(CATEGORIES)],
                        'description': '明确标记的隔离性能样本，通过真实 Store 保存。', 'tags': ['QA'], 'inbox': True})
        seed_seconds = time.perf_counter()-started
        state = measure(store.state)
        status = measure(store.capture_status)
        store.capture_action({'action': 'resume'})
        with fixture.route():
            execution = measure(store.capture_step, 25)
        store.capture_action({'action': 'pause'})
        assert len(store.state()['resources']) == count
        info = store.capture_status()
        assert info['counts']['completed'] == 25 and info['active'] == count-25
        result['datasets'][str(count)] = {'resources': count, 'seedSeconds': round(seed_seconds, 3),
            'fullState': state, 'taskStatus30': status, 'httpFixtureClaimFetchCommit': execution,
            'state': str(store.root), 'limits': 'Local HTTP fixture and paused seeded UI data; not a native FPS measurement'}
    (directory/'backend.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    Path('/tmp/shiji-v6-performance.json').write_text(json.dumps(result))
    print(json.dumps(result, ensure_ascii=False))
finally:
    fixture.close()
