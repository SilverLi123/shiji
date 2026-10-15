import base64
import concurrent.futures
import json
import unittest
import uuid
from unittest.mock import patch

import test_capture_task_api as fixtures
from capture_fixture import png_bytes
from storage import Store


class ClipReceipts(unittest.TestCase):
    setUp = fixtures.CaptureTaskAPI.setUp
    tearDown = fixtures.CaptureTaskAPI.tearDown
    request = fixtures.CaptureTaskAPI.request

    def clip(self, body, **headers):
        return self.request('/api/clip', body, Authorization='Bearer '+self.store.token(), **headers)

    def status(self, rid):
        return self.request('/api/clip/status', {'requestId': rid}, Authorization='Bearer '+self.store.token())

    def body(self):
        return {'requestId': str(uuid.uuid4()), 'url': 'https://example.com/receipt',
                'title': 'Frozen title', 'selection': 'Frozen selection',
                'screenshot': 'data:image/png;base64,'+base64.b64encode(png_bytes()).decode()}

    def test_lost_response_retry_and_status_preserve_later_edits(self):
        body = self.body()
        self.assertEqual(self.status(body['requestId'])[1]['status'], 'not_found')
        code, saved = self.clip(body)
        self.assertEqual(code, 200)
        rid = saved['resource']['id']
        self.assertEqual(saved['receipt'], {'requestId': body['requestId'], 'status': 'saved', 'resourceId': rid})
        self.store.save({'title': 'Curated later', 'notes': 'Replaced notes'}, rid)
        # The server committed, but the sender did not retain its first response.
        before = self.store.get(rid)
        self.store = Store(self.temp.name)
        import server
        server.STORE = self.store
        self.assertEqual(self.status(body['requestId'])[1], saved['receipt'])
        self.assertEqual(self.clip(body)[0], 200)
        self.assertEqual(self.store.get(rid), before)
        self.assertEqual(len(self.store.state()['resources']), 1)
        self.assertEqual(self.store.capture_status()['total'], 1)

    def test_replay_after_trash_or_purge_does_not_resurrect(self):
        body = self.body()
        rid = self.clip(body)[1]['resource']['id']
        self.store.remove(rid)
        self.assertEqual(self.clip(body)[0], 200)
        self.assertTrue(self.store.get(rid)['deleted'])
        # A missing record (e.g. future purge/repair) must not invalidate the
        # transport tombstone. There is no public permanent-delete API today.
        with self.store.connect() as c:
            c.execute('DELETE FROM attachments WHERE resource_id=?', (rid,))
            c.execute('DELETE FROM resources WHERE id=?', (rid,))
        for path in self.store.files.iterdir():
            path.unlink()
        code, result = self.clip(body)
        self.assertEqual(code, 200)
        self.assertEqual(result['receipt']['resourceId'], rid)
        self.assertEqual(self.status(body['requestId'])[1]['status'], 'saved')
        self.assertEqual(self.store.state()['resources'], [])
        self.assertEqual(list(self.store.files.iterdir()), [])

    def test_changed_request_content_rejected_and_same_request_is_atomic(self):
        body = self.body()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.clip(body), range(4)))
        self.assertEqual([code for code, _ in results], [200]*4)
        self.assertEqual(len({row['receipt']['resourceId'] for _, row in results}), 1)
        before = self.store.state()
        self.assertEqual(self.clip({**body, 'selection': 'Changed payload'})[0], 400)
        self.assertEqual(self.store.state(), before)

    def test_receipt_failure_rolls_back_files_resources_and_tasks(self):
        body = self.body()
        # Fail the receipt INSERT after the real attachment and resource writes.
        with self.store.connect() as c:
            c.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON clip_receipts BEGIN SELECT RAISE(ABORT, 'fixture full disk'); END")
        code, _ = self.clip(body)
        self.assertNotEqual(code, 200)
        self.assertEqual(self.store.state()['resources'], [])
        self.assertEqual(self.store.capture_status()['total'], 0)
        self.assertEqual(list(self.store.files.iterdir()), [])
        self.assertEqual(self.status(body['requestId'])[1]['status'], 'not_found')
        with self.store.connect() as c:
            c.execute('DROP TRIGGER fail_receipt')
        self.assertEqual(self.clip(body)[0], 200)

    def test_auth_capability_old_client_and_backup_compatibility(self):
        body = self.body()
        self.assertEqual(self.request('/api/clip/status', {'requestId': body['requestId']})[0], 403)
        self.assertEqual(self.request('/api/clip/status', {'requestId': body['requestId']},
            Authorization='Bearer '+self.store.token(), Origin='https://evil.invalid')[0], 403)
        self.assertEqual(self.request('/api/clip/ping', {}, Authorization='Bearer '+self.store.token())[1]['captureReceipts'], 1)
        code, result = self.clip(body, Origin='chrome-extension://'+'a'*32)
        self.assertEqual(code, 200)
        legacy = {k: v for k, v in body.items() if k != 'requestId'}
        self.assertEqual(self.clip(legacy)[0], 200)
        with self.store.connect() as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 3)
        backup = self.store.create_backup()
        restored = Store(self.temp.name+'/restored')
        restored.restore_zip(self.store.backup_file(backup['name']))
        self.assertEqual(len(restored.state()['resources']), 1)
        self.assertEqual(restored.clip_status({'requestId': body['requestId']})['status'], 'not_found')

    def test_invalid_receipt_requests_save_nothing(self):
        body = self.body()
        for value in ('', None, 'bad', 123):
            self.assertEqual(self.clip({**body, 'requestId': value})[0], 400)
        self.assertEqual(self.request('/api/clip/status', {'requestId': body['requestId'], 'extra': True}, Authorization='Bearer '+self.store.token())[0], 400)
        self.assertEqual(self.store.state()['resources'], [])


if __name__ == '__main__':
    unittest.main()
