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
        # Explicit retry refreshes only the job fence, never the resource's cover.
        job = self.store.capture_status()['tasks'][0]
        with self.fixture.route():
            self.assertFalse(self.store.capture_step())
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'skipped')
        self.store.capture_action({'action': 'retry', 'id': job['id']})
        with self.fixture.route():
            self.assertTrue(self.store.capture_step())
        self.assertEqual(self.fixture.calls, ['/page'])
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
