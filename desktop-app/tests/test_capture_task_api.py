import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from storage import Store
from capture_fixture import Fixture, png_bytes


class CaptureTaskAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.previous = server.STORE
        server.STORE = self.store
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:'+str(self.http.server_port)
        self.fixture = Fixture()

    def tearDown(self):
        self.store.stop_capture_worker()
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(2)
        self.fixture.close()
        server.STORE = self.previous
        self.temp.cleanup()

    def request(self, path, data=None, **headers):
        if data is not None:
            headers['Content-Type'] = 'application/json'
        req = Request(self.base+path, json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as response:
            return response.code, json.load(response)

    def test_quick_capture_reconciles_duplicate_and_enrichment_only_enqueues(self):
        body = {'url': 'http://capture.fixture.invalid/page', 'title': 'capture.fixture.invalid', 'quickCapture': True}
        status, result = self.request('/api/resources', body)
        self.assertEqual(status, 200)
        resource = result['resource']
        self.assertNotIn('quickCapture', resource)
        self.store.save({'title': 'Curated', 'tags': ['New, exact']}, resource['id'])
        status, second = self.request('/api/resources', body)
        self.assertEqual(status, 200)
        self.assertEqual(second['resource']['id'], resource['id'])
        self.assertEqual(second['resource']['title'], 'Curated')
        status, queued = self.request('/api/resources/'+resource['id']+'/enrich', {'url': resource['url'], 'updatedAt': second['resource']['updatedAt']})
        self.assertEqual(status, 200)
        self.assertEqual(queued['status'], 'pending')
        self.assertEqual(self.fixture.calls, [])

    def test_clip_remote_image_does_not_delay_or_undo_durable_page(self):
        body = {'url': 'http://capture.fixture.invalid/page', 'title': 'Browser title', 'imageUrl': 'http://capture.fixture.invalid/invalid-image'}
        status, result = self.request('/api/clip', body, Authorization='Bearer '+self.store.token())
        self.assertEqual(status, 200)
        self.assertEqual(self.fixture.calls, [], 'No network runs inside clip request')
        self.assertEqual(result['resource']['title'], 'Browser title')
        self.assertEqual(self.store.capture_status()['counts']['pending'], 2)
        with self.fixture.route():
            self.store.capture_step('asset')
        self.assertEqual(self.store.get(result['resource']['id'])['title'], 'Browser title')
        self.assertEqual(self.store.capture_status()['counts']['failed'], 1)

    def test_task_api_cancel_pause_retry_and_origin_guard(self):
        self.request('/api/resources', {'url': 'http://capture.fixture.invalid/page', 'title': 'capture.fixture.invalid'})
        status, jobs = self.request('/api/capture/tasks')
        self.assertEqual(status, 200)
        task = jobs['tasks'][0]
        self.assertEqual(self.request('/api/capture/tasks', {'action': 'cancel', 'id': task['id']})[1]['tasks'][0]['status'], 'cancelled')
        self.assertEqual(self.request('/api/capture/tasks', {'action': 'pause'})[1]['paused'], True)
        self.assertEqual(self.request('/api/capture/tasks', {'action': 'resume'})[1]['paused'], False)
        self.assertEqual(self.request('/api/capture/tasks', {'action': 'retry', 'id': task['id']})[1]['tasks'][0]['status'], 'pending')
        self.assertEqual(self.request('/api/capture/tasks', {'action': 'pause'}, Origin='https://evil.invalid')[0], 403)

    def test_screenshot_and_selected_image_preserve_manual_cover_and_exact_notes(self):
        resource = self.store.capture_page({'url': 'http://capture.fixture.invalid/page', 'title': 'Manual'})['resource']
        self.store.attachment(resource['id'], png_bytes(), {'name': 'Manual cover', 'cover': True})
        before = self.store.get(resource['id'])
        import base64
        status, result = self.request('/api/clip', {'url': resource['url'], 'title': 'Incoming', 'selection': 'New, exact', 'screenshot': 'data:image/png;base64,'+base64.b64encode(png_bytes()).decode(), 'imageUrl': 'http://capture.fixture.invalid/image'}, Authorization='Bearer '+self.store.token())
        self.assertEqual(status, 200)
        self.assertEqual(result['resource']['title'], 'Manual')
        self.assertEqual(result['resource']['coverId'], before['coverId'])
        self.assertIn('New, exact', result['resource']['notes'])
        with self.fixture.route():
            self.store.capture_step('asset')
        after = self.store.get(resource['id'])
        self.assertEqual(after['coverId'], before['coverId'])
        self.assertEqual(len(after['attachments']), 2, 'Downloaded bytes already present must be reused')


if __name__ == '__main__':
    unittest.main()
