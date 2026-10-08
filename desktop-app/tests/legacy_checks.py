import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

APP = Path(__file__).resolve().parents[1]
checks = 0


def request(path, method='GET', body=None, expected=200, origin=None):
    global checks
    headers = {'Content-Type': 'application/json'}
    if origin:
        headers['Origin'] = origin
    req = Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    try:
        with urlopen(req) as response:
            status, data = response.status, json.load(response)
    except HTTPError as error:
        status, data = error.code, json.load(error)
    assert status == expected, (path, status, data)
    checks += 1
    return data


def start(data_dir):
    global base
    proc = subprocess.Popen(['python3', str(APP/'server.py'), '--port', '0', '--data-dir', data_dir], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    base = re.search(r'http://\S+', proc.stdout.readline()).group(0)
    return proc


with tempfile.TemporaryDirectory() as temporary:
    process = start(temporary)
    try:
        assert request('/api/resources')['resources'] == []
        raw = {'url': 'https://example.com', 'title': '测试收藏', 'category': '音频', 'tags': ['游戏', '游戏', '中文标签'], 'notes': '用于按钮音效', 'favorite': True, 'inbox': True, 'collection': '测试项目', 'price': '免费', 'license': '待确认'}
        item = request('/api/resources', 'POST', raw)['resource']
        rid = item['id']
        assert item['url'] == 'https://example.com/' and item['tags'] == ['游戏', '中文标签']
        request('/api/resources', 'POST', {**raw, 'url': 'https://EXAMPLE.com:443/#fragment'}, expected=409)
        request('/api/resources', 'POST', {**raw, 'url': 'javascript:alert(1)'}, expected=400)
        changed = request('/api/resources/'+rid, 'PUT', {**item, 'notes': '修改后', 'inbox': False})['resource']
        assert changed['notes'] == '修改后' and changed['createdAt'] == item['createdAt']
        request('/api/collections', 'POST', {'name': '空项目'})
        backup = request('/api/export')
        assert set(backup['collections']) == {'空项目','测试项目'} and backup['resources'][0]['notes'] == '修改后'
        request('/api/resources/'+rid, 'DELETE')
        assert request('/api/resources')['resources'] == []
        request('/api/resources/'+rid+'/restore', 'POST', {})
        assert len(request('/api/resources')['resources']) == 1
        request('/api/import', 'POST', {'version': 1, 'resources': [{**raw, 'url':'https://new.example/'}, {**raw, 'title':''}]}, expected=400)
        assert len(request('/api/resources')['resources']) == 1
        assert request('/api/import', 'POST', backup) == {'added':0, 'skipped':1}
        second = request('/api/resources', 'POST', {**raw, 'url': 'https://second.example/'})['resource']
        request('/api/resources/'+rid, 'PUT', {**changed, 'url': second['url']}, expected=409)
        assert next(x for x in request('/api/resources')['resources'] if x['id']==rid)['url']==item['url']
        request('/api/resources', 'POST', raw, expected=403, origin='https://foreign.example')
        assert request('/api/demo', 'POST', {})['added'] == 8
        demo = next(x for x in request('/api/resources')['resources'] if x['demo'])
        request('/api/resources/'+demo['id'], 'PUT', {**demo, 'demo':False})
        assert request('/api/clear-demo', 'POST', {})['removed'] == 7
        assert len(request('/api/resources')['resources']) == 3
        process.terminate(); process.wait(timeout=5)
        process = start(temporary)
        persisted = request('/api/resources')
        assert len(persisted['resources']) == 3 and '空项目' in persisted['collections']
        request('/api/resources/'+rid, 'DELETE')
        restored = request('/api/import', 'POST', backup)
        assert restored['added']==1
        assert next(x for x in request('/api/resources')['resources'] if x['url']==item['url'])['createdAt']==item['createdAt']
        print(f'PASS: {checks} HTTP checks; CRUD, duplicate prevention, atomic import, backup, collections, undo, demo cleanup, origin protection, restart persistence.')
    finally:
        process.terminate(); process.wait(timeout=5)
