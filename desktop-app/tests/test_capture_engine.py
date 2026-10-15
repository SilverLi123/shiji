import hashlib
import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import Store
from capture import capture_payload, capture_image
from capture_jobs import CaptureFailure
from capture_images import validate_image
from capture_rules import suggest
from capture_fixture import Fixture, png_bytes
from quick_capture import fallback_title


class CaptureEngine(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.fixture = Fixture()

    def tearDown(self):
        self.store.stop_capture_worker()
        self.fixture.close()
        self.temp.cleanup()

    def save(self, path='/page', **changes):
        url = 'http://capture.fixture.invalid'+path
        return self.store.save({'url': url, 'title': fallback_title(url), **changes})['resource']

    def test_real_http_metadata_local_cover_and_explicit_suggestions(self):
        resource = self.save()
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        current = self.store.get(resource['id'])
        self.assertEqual(current['title'], 'React Component Library')
        self.assertEqual(current['description'], 'Useful React UI components')
        self.assertEqual(current['sourceUrl'], resource['url'])
        self.assertEqual(current['favicon'], 'http://capture.fixture.invalid/icon.png')
        self.assertEqual(current['thumbnail'], '')
        self.assertEqual(current['tags'], [])
        self.assertEqual(current['category'], '其他')
        attachment = current['attachments'][0]
        self.assertEqual(current['coverId'], attachment['id'])
        self.assertEqual((self.store.files/attachment['id']).read_bytes(), png_bytes())
        self.assertEqual(attachment['sha256'], hashlib.sha256(png_bytes()).hexdigest())
        job = self.store.capture_status()['tasks'][0]
        self.assertEqual(job['suggestions']['tags'], ['React', '组件'])
        self.store.capture_action({'action': 'accept', 'id': job['id'], 'updatedAt': current['updatedAt']})
        self.assertEqual(self.store.get(resource['id'])['category'], 'UI / 设计')
        self.assertEqual(self.store.get(resource['id'])['tags'], ['React', '组件'])

    def test_suggestions_ignore_persists_and_never_silently_overwrites(self):
        resource = self.save(category='灵感', tags=['New, exact'])
        with self.fixture.route():
            self.store.capture_step()
        current = self.store.get(resource['id'])
        job = self.store.capture_status()['tasks'][0]
        self.store.capture_action({'action': 'ignore', 'id': job['id'], 'updatedAt': current['updatedAt']})
        self.assertEqual(Store(self.temp.name).capture_status()['tasks'][0]['suggestionState'], 'ignored')
        self.assertEqual(self.store.get(resource['id'])['tags'], ['New, exact'])
        self.assertEqual(self.store.get(resource['id'])['category'], '灵感')

    def test_stale_suggestion_accept_cannot_overwrite_new_edit(self):
        resource = self.save()
        with self.fixture.route():
            self.store.capture_step()
        current = self.store.get(resource['id'])
        job = self.store.capture_status()['tasks'][0]
        self.store.save({'category': '音频', 'tags': ['Mine']}, resource['id'])
        with self.assertRaises(ValueError):
            self.store.capture_action({'action': 'accept', 'id': job['id'], 'updatedAt': current['updatedAt']})
        self.assertEqual(self.store.get(resource['id'])['category'], '音频')

    def test_invalid_cover_keeps_metadata_and_poster_without_attachment(self):
        resource = self.save('/bad-cover')
        with self.fixture.route():
            self.assertFalse(self.store.capture_step())
        current = self.store.get(resource['id'])
        self.assertEqual(current['title'], 'React Component Library')
        self.assertEqual(current['attachments'], [])
        self.assertEqual(current['coverId'], '')
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'failed')
        self.assertEqual(list(self.store.files.iterdir()), [])

    def test_incomplete_metadata_keeps_usable_resource(self):
        resource = self.save('/incomplete')
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        self.assertEqual(self.store.get(resource['id'])['title'], resource['title'])
        self.assertEqual(self.store.get(resource['id'])['attachments'], [])

    def test_redirect_canonical_is_a_hint_and_saved_url_stays_stable(self):
        resource = self.save('/redirect')
        with self.fixture.route():
            self.store.capture_step()
            meta = capture_payload(resource['url'])['metadata']
        self.assertEqual(self.store.get(resource['id'])['url'], resource['url'])
        self.assertEqual(meta['canonicalUrl'], 'http://capture.fixture.invalid/canonical')
        self.assertEqual(self.store.get(resource['id'])['sourceUrl'], 'http://capture.fixture.invalid/page')

    def test_private_redirect_is_blocked_with_no_late_writes(self):
        resource = self.save('/redirect-private')
        with self.fixture.route():
            self.assertFalse(self.store.capture_step())
        self.assertEqual(self.store.get(resource['id']), resource)
        self.assertNotIn('/private', self.fixture.calls)
        self.assertEqual(self.store.capture_status()['tasks'][0]['errorCode'], 'blocked')

    def test_timeout_and_dns_failure_are_retryable(self):
        resource = self.save('/slow')
        with self.fixture.route(timeout=.05):
            self.store.capture_step()
        self.assertEqual(self.store.get(resource['id']), resource)
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'retry')
        with patch('capture.public_fetch', side_effect=socket.gaierror('private content must not leak')):
            with self.assertRaises(CaptureFailure) as error:
                capture_payload(resource['url'])
        self.assertEqual(error.exception.code, 'dns')
        self.assertNotIn('private content', error.exception.message)

    def test_manual_cover_before_work_prevents_image_fetch(self):
        resource = self.save()
        self.store.attachment(resource['id'], png_bytes(), {'name': 'Manual', 'cover': True})
        # Retry never rebases a task over an intervening manual cover edit.
        job = self.store.capture_status()['tasks'][0]
        with self.fixture.route():
            self.assertFalse(self.store.capture_step())
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'skipped')
        self.store.capture_action({'action': 'retry', 'id': job['id']})
        with self.fixture.route():
            self.assertFalse(self.store.capture_step())
        self.assertEqual(self.fixture.calls, [])
        self.assertEqual(len(self.store.get(resource['id'])['attachments']), 1)

    def test_manual_edits_delete_url_change_or_cover_during_real_fetch_win(self):
        for field in ('title', 'category', 'cover', 'delete', 'url'):
            with self.subTest(field=field):
                resource = self.save('/page/'+field)
                entered, release = threading.Event(), threading.Event()
                import capture
                original = capture.capture_payload
                def delayed(*args):
                    payload = original(*args)
                    entered.set()
                    release.wait(2)
                    return payload
                with self.fixture.route(), patch('capture.capture_payload', side_effect=delayed):
                    thread = threading.Thread(target=self.store.capture_step)
                    thread.start()
                    self.assertTrue(entered.wait(1))
                    if field == 'cover':
                        self.store.attachment(resource['id'], png_bytes(), {'name': 'Mine', 'cover': True})
                    elif field == 'delete':
                        self.store.remove(resource['id'])
                    else:
                        self.store.save({field: {'title': 'Manual', 'category': '音频', 'url': 'http://capture.fixture.invalid/incomplete'}[field]}, resource['id'])
                    expected = self.store.get(resource['id'])
                    release.set()
                    thread.join(2)
                self.assertEqual(self.store.get(resource['id']), expected)

    def test_cover_retry_deduplicates_identical_existing_bytes(self):
        resource = self.save()
        self.store.attachment(resource['id'], png_bytes(), {'name': 'Already downloaded', 'cover': False})
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        current = self.store.get(resource['id'])
        self.assertEqual(len(current['attachments']), 1)
        self.assertEqual(current['coverId'], current['attachments'][0]['id'])

    def test_image_type_crc_and_truncation_checks(self):
        raw = png_bytes()
        self.assertEqual(validate_image(raw, 'image/png'), 'image/png')
        for candidate, mime in ((raw, 'text/html'), (raw[:24], 'image/png'), (raw[:-1]+b'x', 'image/png'), (b'\xff\xd8\xff\xe0noJPEG', 'image/jpeg')):
            with self.subTest(mime=mime), self.assertRaises(ValueError):
                validate_image(candidate, mime)
        with self.fixture.route(), self.assertRaises(CaptureFailure):
            capture_image('http://capture.fixture.invalid/wrong-type')

    def test_invalid_jpeg_scan_and_indexed_png_are_rejected(self):
        import struct, zlib
        def chunk(name, raw):
            return struct.pack('>I', len(raw))+name+raw+struct.pack('>I', zlib.crc32(name+raw) & 0xffffffff)
        import base64
        jpeg = base64.b64decode('/9j/wAALCAABAAEBAREA/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9sAQwACAgICAgIDAgIDBQMDAwUGBQUFBQYIBgYGBgYICggICAgICAoKCgoKCgoKDAwMDAwMDg4ODg4PDw8PDw8PDw8P/90ABAAB/9oACAEBAAA/AP38r//Z')
        self.assertEqual(validate_image(jpeg, 'image/jpeg'), 'image/jpeg')
        scan = jpeg.index(b'\xff\xda')
        scan_end = scan+2+int.from_bytes(jpeg[scan+2:scan+4], 'big')
        with self.assertRaises(ValueError):
            validate_image(jpeg[:scan_end]+b'\xff\xd9', 'image/jpeg')
        indexed = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 3, 0, 0, 0))
        pixels = chunk(b'IDAT', zlib.compress(b'\0\0'))+chunk(b'IEND', b'')
        self.assertEqual(validate_image(indexed+chunk(b'PLTE', b'\xff\0\0')+pixels, 'image/png'), 'image/png')
        for raw, mime in ((indexed+pixels, 'image/png'),
                          (indexed+chunk(b'PLTE', b'\xff')+pixels, 'image/png'),
                          (bytes.fromhex('ffd8 ffc0 0008 08 0001 0001 00 ffda 0002 ffd9'), 'image/jpeg')):
            with self.subTest(mime=mime), self.assertRaises(ValueError):
                validate_image(raw, mime)

    def test_non_cover_asset_publication_marks_snapshot_dirty(self):
        resource = self.save()
        self.store.attachment(resource['id'], png_bytes(), {'name': 'Manual', 'cover': True})
        current = self.store.get(resource['id'])
        with self.store.connect() as c:
            self.store.enqueue_capture(c, current, 'asset', {'url': 'http://capture.fixture.invalid/image'})
        # Use a different valid image so the existing cover is not reused.
        import struct, zlib
        def chunk(name, raw):
            return struct.pack('>I', len(raw))+name+raw+struct.pack('>I', zlib.crc32(name+raw) & 0xffffffff)
        raw = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0))+chunk(b'IDAT', zlib.compress(b'\0\x80'))+chunk(b'IEND', b'')
        self.store.create_snapshot()
        self.assertFalse(self.store.dirty)
        with patch('capture_jobs.fetch_payload', return_value={'image': (raw, 'http://capture.fixture.invalid/image', 'OG Image')}):
            self.assertTrue(self.store.capture_step('asset'))
        self.assertEqual(self.store.get(resource['id'])['coverId'], current['coverId'])
        self.assertEqual(len(self.store.get(resource['id'])['attachments']), 2)
        self.assertTrue(self.store.dirty, 'Downloaded attachment must trigger automatic snapshot')
        self.store.create_snapshot()
        self.assertFalse(self.store.dirty)

    def test_worker_processing_exception_does_not_stop_later_jobs(self):
        import time
        self.save('/worker-first')
        self.save('/worker-second')
        import capture_jobs
        original = capture_jobs.fetch_payload
        calls = []
        def fails_once(*args):
            calls.append(args[0]['id'])
            if len(calls) == 1: raise RuntimeError('Do not leak URL or remote content')
            return original(*args)
        with self.fixture.route(), patch('capture_jobs.fetch_payload', side_effect=fails_once):
            self.store.start_capture_worker()
            deadline = time.monotonic()+4
            while self.store.capture_status()['counts']['completed'] != 1 and time.monotonic() < deadline:
                time.sleep(.02)
            self.store.stop_capture_worker()
        state = self.store.capture_status()
        self.assertEqual(state['counts']['retry'], 1)
        self.assertEqual(state['counts']['completed'], 1)
        self.assertTrue(all('Do not leak' not in task['error'] for task in state['tasks']))

    def test_rules_use_exact_domains_and_canonical_tags(self):
        expected = {'https://github.com/owner/repo': ['GitHub'], 'https://huggingface.co/model': ['AI', '模型'], 'https://polyhaven.com/': ['3D', '素材'], 'https://gsap.com/': ['动效', '前端']}
        for url, tags in expected.items():
            self.assertEqual(suggest({'url': url}, {})['tags'], tags)
        self.assertEqual(suggest({'url': 'https://notgithub.com/'}, {}), {})

    def test_jobs_do_not_enter_manifest2_restore_or_sync_authority(self):
        resource = self.save()
        with self.fixture.route():
            self.store.capture_step()
        raw = self.store.backup_bytes()
        other_temp = tempfile.TemporaryDirectory()
        try:
            other = Store(other_temp.name)
            other.restore_zip(raw)
            self.assertEqual(other.state()['resources'][0]['title'], 'React Component Library')
            self.assertEqual(other.state()['resources'][0]['attachments'][0]['sha256'], hashlib.sha256(png_bytes()).hexdigest())
            self.assertEqual(other.capture_status()['tasks'], [])
        finally:
            other_temp.cleanup()


if __name__ == '__main__':
    unittest.main()
