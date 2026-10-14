import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import Store, Duplicate
from quick_capture import fallback_title


class CaptureJobs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.url = 'https://example.com/item'

    def tearDown(self):
        if hasattr(self.store, 'stop_capture_worker'):
            self.store.stop_capture_worker()
        self.temp.cleanup()

    def save(self):
        return self.store.save({'url': self.url, 'title': fallback_title(self.url), 'inbox': True})['resource']

    def test_save_and_job_survive_restart_without_changing_exchange(self):
        resource = self.save()
        other = Store(self.temp.name)
        jobs = other.capture_status()['tasks']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['status'], 'pending')
        self.assertEqual(jobs[0]['resourceId'], resource['id'])
        self.assertEqual(jobs[0]['resourceVersion'], resource['updatedAt'])
        self.assertEqual(other.get(resource['id']), resource)
        self.assertNotIn('captureJobs', other.export())
        with other.connect() as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 3)

    def test_repeated_url_and_enqueue_do_not_duplicate_resource_or_job(self):
        resource = self.save()
        with self.assertRaises(Duplicate):
            self.save()
        body = {'url': resource['url'], 'updatedAt': resource['updatedAt']}
        first = self.store.request_capture(resource['id'], body)
        second = self.store.request_capture(resource['id'], body)
        self.assertEqual(first['task']['id'], second['task']['id'])
        self.assertEqual(len(self.store.capture_status()['tasks']), 1)
        self.assertEqual(len(self.store.state()['resources']), 1)

    def test_job_insert_failure_rolls_back_resource_save(self):
        self.store.capture_status()  # ensure task schema exists before trigger
        with self.store.connect() as c:
            c.execute("CREATE TRIGGER fail_capture BEFORE INSERT ON capture_jobs BEGIN SELECT RAISE(ABORT,'QA queue unavailable'); END")
        with self.assertRaises(Exception):
            self.save()
        self.assertEqual(self.store.state()['resources'], [])
        self.assertEqual(self.store.capture_status()['tasks'], [])

    def test_cancel_survives_restart_and_keeps_durable_resource(self):
        resource = self.save()
        task = self.store.capture_status()['tasks'][0]
        self.store.capture_action({'action': 'cancel', 'id': task['id']})
        other = Store(self.temp.name)
        self.assertEqual(other.capture_status()['tasks'][0]['status'], 'cancelled')
        self.assertEqual(other.get(resource['id']), resource)

    def test_pause_is_persistent(self):
        self.save()
        self.store.capture_action({'action': 'pause'})
        self.assertTrue(Store(self.temp.name).capture_status()['paused'])
        self.assertFalse(self.store.capture_step())
        self.store.capture_action({'action': 'resume'})
        self.assertFalse(self.store.capture_status()['paused'])

    def test_expired_running_lease_is_recovered_and_stale_owner_cannot_finish(self):
        self.save()
        task = self.store.capture_status()['tasks'][0]
        with self.store.connect() as c:
            c.execute("UPDATE capture_jobs SET status='running',attempts=1,lease='dead-owner',lease_until=? WHERE id=?", (time.time()-1, task['id']))
        other = Store(self.temp.name)
        status = other.capture_status()['tasks'][0]
        self.assertEqual(status['status'], 'retry')
        self.assertEqual(status['attempts'], 1)

    def test_cancel_and_pause_discard_late_network_results(self):
        for action in ('cancel', 'pause'):
            with self.subTest(action=action):
                self.url += '/next'
                resource = self.save()
                task = next(j for j in self.store.capture_status()['tasks'] if j['resourceId'] == resource['id'])
                entered, release = threading.Event(), threading.Event()
                def network(item, kind, options):
                    entered.set()
                    self.assertTrue(release.wait(2))
                    return {'metadata': {'title': 'Late title', 'description': 'Late description'}}
                with patch('capture_jobs.fetch_payload', side_effect=network):
                    thread = threading.Thread(target=self.store.capture_step)
                    thread.start()
                    self.assertTrue(entered.wait(1))
                    self.store.capture_action({'action': action, **({'id': task['id']} if action == 'cancel' else {})})
                    release.set()
                    thread.join(2)
                    self.assertFalse(thread.is_alive())
                self.assertEqual(self.store.get(resource['id']), resource)
                if action == 'pause':
                    self.store.capture_action({'action': 'resume'})

    def test_network_does_not_hold_global_lock_and_any_manual_edit_wins(self):
        resource = self.save()
        entered, release = threading.Event(), threading.Event()
        def network(item, kind, options):
            entered.set()
            release.wait(2)
            return {'metadata': {'title': 'Late title', 'description': 'Late description'}}
        with patch('capture_jobs.fetch_payload', side_effect=network):
            thread = threading.Thread(target=self.store.capture_step)
            thread.start()
            self.assertTrue(entered.wait(1))
            self.store.save({'title': '手动标题', 'category': '灵感', 'tags': ['New, exact'], 'notes': '保留'}, resource['id'])
            release.set()
            thread.join(2)
        current = self.store.get(resource['id'])
        self.assertEqual(current['title'], '手动标题')
        self.assertEqual(current['description'], '')
        self.assertEqual(current['tags'], ['New, exact'])
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'skipped')

    def test_transient_failure_retries_then_survives_restart_and_manual_retry(self):
        self.save()
        from capture_jobs import CaptureFailure
        task_id = self.store.capture_status()['tasks'][0]['id']
        with patch('capture_jobs.fetch_payload', side_effect=CaptureFailure('timeout', '网络超时，原收藏已保留。')):
            for attempt in range(3):
                with self.store.connect() as c:
                    c.execute('UPDATE capture_jobs SET next_at=0 WHERE id=?', (task_id,))
                self.assertFalse(self.store.capture_step())
        task = Store(self.temp.name).capture_status()['tasks'][0]
        self.assertEqual(task['status'], 'failed')
        self.assertEqual(task['attempts'], 3)
        self.assertEqual(len(self.store.state()['resources']), 1)
        self.store.capture_action({'action': 'retry', 'id': task_id})
        with patch('capture_jobs.fetch_payload', return_value={'metadata': {'title': 'Recovered'}}):
            self.assertTrue(self.store.capture_step())
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'completed')

    def test_new_worker_lease_fences_old_return(self):
        resource = self.save()
        entered, release = threading.Event(), threading.Event()
        def old_network(item, kind, options):
            entered.set()
            release.wait(2)
            return {'metadata': {'title': 'Old owner'}}
        other = Store(self.temp.name)
        with patch('capture_jobs.fetch_payload', side_effect=old_network):
            thread = threading.Thread(target=self.store.capture_step)
            thread.start()
            self.assertTrue(entered.wait(1))
            with self.store.connect() as c:
                c.execute("UPDATE capture_jobs SET lease_until=0 WHERE resource_id=?", (resource['id'],))
            with patch('capture_jobs.fetch_payload', return_value={'metadata': {'title': 'New owner'}}):
                self.assertTrue(other.capture_step())
            release.set()
            thread.join(2)
        self.assertEqual(self.store.get(resource['id'])['title'], 'New owner')
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'completed')

    def test_retry_and_repeat_request_cannot_rebase_over_manual_edits(self):
        resource = self.save()
        task = self.store.capture_status()['tasks'][0]
        self.store.capture_action({'action': 'cancel', 'id': task['id']})
        manual = self.store.save({'title': fallback_title(self.url), 'notes': 'Manual edit, even with the same fallback title'}, resource['id'])['resource']
        self.store.capture_action({'action': 'retry', 'id': task['id']})
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'skipped')
        result = self.store.request_capture(resource['id'], {'url': manual['url'], 'updatedAt': manual['updatedAt']})
        self.assertEqual(result['status'], 'skipped')
        with patch('capture_jobs.fetch_payload') as network:
            self.assertFalse(self.store.capture_step())
            network.assert_not_called()
        self.assertEqual(self.store.get(resource['id']), manual)
        self.assertEqual(len(self.store.capture_status()['tasks']), 1)

    def test_delete_restore_during_fetch_invalidates_old_lease(self):
        resource = self.save()
        entered, release = threading.Event(), threading.Event()
        def network(item, kind, options):
            entered.set()
            release.wait(2)
            return {'metadata': {'title': 'Must not survive delete'}}
        with patch('capture_jobs.fetch_payload', side_effect=network):
            thread = threading.Thread(target=self.store.capture_step)
            thread.start()
            self.assertTrue(entered.wait(1))
            self.store.remove(resource['id'])
            self.store.remove(resource['id'], True)
            release.set()
            thread.join(2)
        self.assertEqual(self.store.get(resource['id']), resource)
        self.assertEqual(self.store.capture_status()['tasks'][0]['status'], 'skipped')

    def test_disabled_preview_status_does_not_create_phantom_tasks(self):
        self.save()
        self.assertEqual(self.store.preview_status()['pending'], 1)
        self.assertEqual(len(self.store.capture_status()['tasks']), 1)
        self.store.configure_previews({'enabled': True})
        self.assertEqual(len(self.store.capture_status()['tasks']), 2)
        self.store.configure_previews({'enabled': False})
        self.assertEqual(self.store.capture_status()['active'], 1)
        self.store.configure_previews({'enabled': True})
        self.assertEqual(self.store.capture_status()['active'], 2)


if __name__ == '__main__':
    unittest.main()
