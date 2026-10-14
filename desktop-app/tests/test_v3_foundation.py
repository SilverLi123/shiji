"""Real ephemeral HTTP/SQLite -> retained renderer -> ZIP contracts across both branches."""
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from storage import Store
from quick_capture import fallback_title

class V3FoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='shiji-v3-http-')
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.store_patch = patch.object(server, 'STORE', self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        class Quiet(server.Handler):
            def log_message(self, *args): pass
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_http)
        self.base = 'http://127.0.0.1:' + str(self.http.server_port)

    def stop_http(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(3)

    def request(self, method, path, body=None, headers=None):
        headers = dict(headers or {})
        data = None
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            headers.setdefault('Content-Type', 'application/octet-stream' if isinstance(body, bytes) else 'application/json')
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
            return json.loads(raw) if 'application/json' in response.headers.get('Content-Type', '') else raw

    def resource(self):
        url = 'https://github.com/SilverLi123/shiji'
        return self.request('POST', '/api/resources', {'title': fallback_title(url), 'url': url, 'category': '开发工具', 'inbox': True})['resource']

    def image(self):
        return (Path(__file__).resolve().parents[1] / 'static/previews/polyhaven.jpg').read_bytes()

    def attach(self, rid):
        metadata = base64.b64encode(json.dumps({'name': 'v3-preview.jpg', 'cover': True}).encode()).decode()
        self.request('POST', '/api/resources/' + rid + '/attachments', self.image(), {'X-Metadata': metadata})
        return self.store.get(rid)['coverId']

    def test_v51_capture_enrich_during_press_keeps_original_click(self):
        release=threading.Event()
        original=server.Handler.do_POST
        def post(handler):
            if handler.path=='/qa-release':
                release.set();body=b'{}';handler.send_response(200);handler.send_header('Content-Length',str(len(body)));handler.end_headers();handler.wfile.write(body)
            else:original(handler)
        def metadata(url, cover_url='', need_cover=True):
            if not release.wait(10):raise RuntimeError('metadata release deadline')
            return {'metadata':{'title':'已补全的真实资源','description':'Controlled network result; actual storage enrichment'},'image':None}
        try:
            with patch.object(server.Handler,'do_POST',post),patch('capture.capture_payload',side_effect=metadata):
                self.store.start_capture_worker()
                result=subprocess.run(['node',str(Path(__file__).with_name('v51_capture_click.cjs'))],input=json.dumps({'base':self.base}),text=True,capture_output=True,timeout=20)
        finally:
            release.set()
            self.store.stop_capture_worker()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('one original detail click',result.stdout)

    def test_capture_survives_offline_and_manual_edit_then_real_fields_reach_renderer(self):
        row = self.resource()
        rid = row['id']
        original = {'url': row['url'], 'updatedAt': row['updatedAt']}
        self.assertEqual(Store(self.tmp.name).get(rid)['title'], 'SilverLi123/shiji · GitHub')
        from capture_jobs import CaptureFailure
        self.assertEqual(self.request('POST', '/api/resources/' + rid + '/enrich', original)['status'], 'pending')
        with patch('capture.capture_payload', side_effect=CaptureFailure('network','连接暂时失败，原收藏已保留。')):
            self.assertFalse(self.store.capture_step())
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'],'retry')
        self.assertEqual(self.store.get(rid),row)
        self.request('PUT', '/api/resources/' + rid, {'title': 'V3 精确收藏', 'tags': ['New, exact'], 'notes': 'Preserved detail', 'language': 'Swift', 'favorite': True})
        with patch('capture.metadata', side_effect=AssertionError('stale request must not fetch')):
            self.assertEqual(self.request('POST', '/api/resources/' + rid + '/enrich', original)['status'], 'skipped')
        aid = self.attach(rid)
        self.assertEqual(self.request('GET', '/api/files/' + aid), self.image())
        self.request('POST', '/api/resources', {'title': 'QA prompt', 'kind': 'prompt', 'snippet': 'Exact <prompt>', 'category': '灵感'})
        detail = self.request('GET', '/api/resources/' + rid)['resource']
        self.assertEqual(detail['notes'], 'Preserved detail')
        self.assertEqual(detail['tags'], ['New, exact'])
        state = self.request('GET', '/api/resources')
        result = subprocess.run(['node', str(Path(__file__).with_name('v3_resource_contract.cjs'))], input=json.dumps({'resources': state['resources'], 'id': rid, 'attachmentId': aid}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run(['node', str(Path(__file__).with_name('v5_resource_contract.cjs'))], input=json.dumps({'resources': state['resources'], 'id': rid, 'attachmentId': aid}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.store.preview_status()['enabled'])

    def test_zip_preflight_cancel_is_read_only_and_confirm_restores_identity_and_bytes(self):
        rid = self.resource()['id']
        self.request('PUT', '/api/resources/' + rid, {'tags': ['New, exact']})
        aid = self.attach(rid)
        backup = self.request('POST', '/api/backups', {})
        archive = self.request('GET', '/api/backups/' + backup['name'])
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            self.assertEqual(json.loads(z.read('manifest.json'))['version'], 2)
            self.assertEqual(z.read('files/' + aid), self.image())
        self.request('DELETE', '/api/resources/' + rid)
        before = self.store.state(True)
        preview = self.request('POST', '/api/restore/preflight', archive)
        self.assertEqual(preview['summary']['active'], 1)
        self.assertEqual(self.store.state(True), before)
        self.request('POST', '/api/restore/cancel', {'ticket': preview['ticket']})
        self.assertEqual(self.store.state(True), before)
        preview = self.request('POST', '/api/backups/preflight', {'name': backup['name']})
        confirm = {'ticket': preview['ticket'], 'confirm': True}
        self.request('POST', '/api/restore/confirm', confirm)
        self.assertFalse(self.store.get(rid)['deleted'])
        self.assertEqual(self.store.get(rid)['tags'], ['New, exact'])
        self.assertEqual(self.request('GET', '/api/files/' + aid), self.image())
        with self.store.connect() as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0], 3)
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request('POST', '/api/restore/confirm', confirm)
        self.assertEqual(raised.exception.code, 400)

    def test_http_batch_undo_preserves_resource_and_attachment_identity(self):
        row = self.resource()
        aid = self.attach(row['id'])
        before = self.store.get(row['id'])
        receipt = self.request('POST', '/api/batch', {'action': 'delete', 'ids': [row['id']]})
        self.assertTrue(self.store.get(row['id'])['deleted'])
        self.request('POST', '/api/undo', {'token': receipt['undoToken']})
        self.assertEqual(self.store.get(row['id']), before)
        self.assertEqual(self.request('GET', '/api/files/' + aid), self.image())

    def test_cross_origin_write_is_rejected_without_mutating_library(self):
        before = self.store.state()
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request('POST', '/api/resources', {'title': 'Rejected'}, {'Origin': 'https://example.com'})
        self.assertEqual(raised.exception.code, 403)
        self.assertEqual(self.store.state(), before)

if __name__ == '__main__': unittest.main()
