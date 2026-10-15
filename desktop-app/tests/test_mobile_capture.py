"""Real phone-shaped sync writes through Store and the public-page HTTP fixture."""
import copy
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch

from storage import Store
from mobile_sync import SyncEngine
from capture_fixture import Fixture, png_bytes


class MobileCapture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.sync = SyncEngine(self.store)
        self.fixture = Fixture()

    def tearDown(self):
        self.store.stop_capture_worker()
        self.fixture.close()
        self.temp.cleanup()

    def record(self, path='/page', **fields):
        return {'id': str(uuid.uuid4()), 'title': 'capture.fixture.invalid',
                'url': 'http://capture.fixture.invalid'+path, 'kind': 'website',
                'createdAt': '2026-10-07T01:00:00Z', 'attachments': [],
                'deleted': False, **fields}

    def body(self, resources):
        snapshot = self.sync.snapshot()
        return {'version': 1, 'libraryId': snapshot['libraryId'],
                'expectedRevision': snapshot['revision'],
                'requestId': str(uuid.uuid4()), 'resources': resources}

    def test_new_phone_url_enriches_and_returns_local_cover_in_sync_snapshot(self):
        record = self.record(tags=['New, exact'], notes='Phone notes')
        body = self.body([record])
        saved = self.sync.commit(body)
        self.assertEqual(self.store.capture_status()['counts']['pending'], 1)
        self.assertEqual(self.fixture.calls, [], 'Sync must persist before network')
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        current = self.sync.snapshot()['resources'][0]
        self.assertEqual(current['id'], record['id'])
        self.assertEqual(current['title'], 'React Component Library')
        self.assertEqual(current['notes'], 'Phone notes')
        self.assertEqual(current['tags'], ['New, exact'])
        self.assertEqual(self.sync.file(current['coverId'])[0], png_bytes())
        self.assertNotEqual(saved['revision'], self.sync.snapshot()['revision'])
        self.sync.commit(body)  # replay old response must not undo enrichment
        self.assertEqual(self.store.capture_status()['total'], 1)
        self.assertEqual(self.store.get(record['id']), current)
        self.assertEqual(Store(self.temp.name).capture_status()['counts']['completed'], 1)

    def test_curated_phone_fields_and_cover_are_preserved(self):
        record = self.record(title='My title', description='My description', tags=['Mine'], category='灵感')
        import hashlib
        aid = str(uuid.uuid4())
        raw = png_bytes()
        self.sync.stage(aid, raw, hashlib.sha256(raw).hexdigest())
        record.update(coverId=aid, attachments=[{'id': aid, 'resourceId': record['id'],
            'name': 'Mine.png', 'mime': 'image/png', 'size': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(), 'license': '待确认', 'colors': []}])
        self.sync.commit(self.body([record]))
        self.assertEqual(self.store.capture_status()['total'], 1)
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        current = self.store.get(record['id'])
        for key in ('title', 'description', 'tags', 'category', 'coverId'):
            self.assertEqual(current[key], record[key])
        self.assertEqual(len(current['attachments']), 1)
        self.assertNotIn('/image', self.fixture.calls)

    def test_url_change_only_and_no_bulk_recapture(self):
        record = self.record()
        first = self.sync.commit(self.body([record]))['resources'][0]
        with self.fixture.route():
            self.store.capture_step()
        current = self.sync.snapshot()['resources'][0]
        self.sync.commit(self.body([{**current, 'notes': 'Organized on phone'}]))
        self.assertEqual(self.store.capture_status()['total'], 1)
        current = self.sync.snapshot()['resources'][0]
        self.sync.commit(self.body([{**current, 'url': 'http://capture.fixture.invalid/incomplete'}]))
        self.assertEqual(self.store.capture_status()['total'], 2)
        deleted = self.record('/deleted', deleted=True)
        note = self.record('/note', kind='prompt', url='')
        self.sync.commit(self.body([deleted, note]))
        self.assertEqual(self.store.capture_status()['total'], 2)

    def test_sync_edit_or_delete_during_parsing_rejects_late_result(self):
        import capture
        original = capture.capture_payload
        for deleted in (False, True):
            record = self.record('/page/'+str(deleted))
            self.sync.commit(self.body([record]))
            entered, release = threading.Event(), threading.Event()
            def delayed(*args):
                result = original(*args)
                entered.set()
                release.wait(3)
                return result
            with self.fixture.route(), patch('capture.capture_payload', side_effect=delayed):
                thread = threading.Thread(target=self.store.capture_step)
                thread.start()
                try:
                    self.assertTrue(entered.wait(2))
                    current = self.store.get(record['id'])
                    current.update(title='Latest phone edit', deleted=deleted)
                    self.sync.commit(self.body([current]))
                finally:
                    release.set()
                    thread.join(3)
            current = self.store.get(record['id'])
            self.assertEqual(current['title'], 'Latest phone edit')
            self.assertEqual(current['deleted'], deleted)
            self.assertEqual(current['attachments'], [])
        self.assertEqual(self.store.capture_status()['counts']['skipped'], 2)

    def test_enqueue_failure_rolls_back_sync_and_retry_receipt(self):
        record = self.record()
        body = self.body([record])
        before = self.sync.snapshot()
        with patch.object(self.store, 'enqueue_capture', side_effect=RuntimeError('disk unavailable')):
            with self.assertRaises(RuntimeError):
                self.sync.commit(body)
        self.assertEqual(self.sync.snapshot(), before)
        self.sync.commit(body)
        self.assertEqual(self.store.capture_status()['total'], 1)


if __name__ == '__main__':
    unittest.main()
