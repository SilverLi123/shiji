"""Compatibility UI for opt-in legacy previews, backed by the unified task engine."""
import json
import time


class PreviewOperations:
    def init_previews(self):
        with self.connect() as c:
            row = c.execute('SELECT value FROM settings WHERE key="websitePreviews"').fetchone()
        self._preview_config = json.loads(row['value']) if row else {'enabled': False, 'paused': False, 'interval': 30}
        self._preview_generation = 0
        self._preview_next = 0
        if not self._preview_config['enabled']:
            with self.connect() as c:
                c.execute("UPDATE capture_jobs SET status='skipped',lease='',lease_until=0,error_code='disabled',error='网站预览已关闭。' WHERE kind='preview' AND status IN ('pending','running','retry')")

    def _queue_legacy_previews(self):
        if not self._preview_config['enabled']:
            return
        with self.lock, self.connect() as c:
            candidates = c.execute("""SELECT r.payload FROM resources r WHERE r.deleted=0
                AND json_extract(r.payload,'$.kind')='website'
                AND coalesce(json_extract(r.payload,'$.coverId'),'')=''
                AND coalesce(json_extract(r.payload,'$.thumbnail'),'')=''
                AND NOT EXISTS(SELECT 1 FROM capture_jobs j WHERE j.resource_id=r.id
                    AND j.url=json_extract(r.payload,'$.url') AND j.kind='preview')
                ORDER BY r.rowid LIMIT 100""").fetchall()
            for row in candidates:
                self.enqueue_capture(c, json.loads(row['payload']), 'preview')

    def preview_status(self):
        from capture import chrome_binary
        self._queue_legacy_previews()
        with self.lock, self.connect() as c:
            rows = c.execute("SELECT status,count(*) FROM capture_jobs WHERE kind='preview' GROUP BY status").fetchall()
            counts = {r[0]: r[1] for r in rows}
            candidates = c.execute("SELECT count(*) FROM resources r WHERE r.deleted=0 AND json_extract(r.payload,'$.kind')='website' AND coalesce(json_extract(r.payload,'$.coverId'),'')='' AND coalesce(json_extract(r.payload,'$.thumbnail'),'')='' AND NOT EXISTS(SELECT 1 FROM capture_jobs j WHERE j.resource_id=r.id AND j.url=json_extract(r.payload,'$.url') AND j.kind='preview')").fetchone()[0]
            failures = c.execute("SELECT j.resource_id AS id,json_extract(r.payload,'$.title') AS title,j.error AS message FROM capture_jobs j LEFT JOIN resources r ON r.id=j.resource_id WHERE j.kind='preview' AND j.status IN ('retry','failed') ORDER BY j.updated_at DESC LIMIT 5").fetchall()
            return {**self._preview_config, 'running': bool(counts.get('running', 0)),
                    'completed': counts.get('completed', 0),
                    'pending': candidates + sum(counts.get(s, 0) for s in ('pending', 'running', 'retry')),
                    'failed': sum(counts.get(s, 0) for s in ('retry', 'failed')),
                    'failures': [dict(row) for row in failures], 'chromeAvailable': bool(chrome_binary())}

    def configure_previews(self, body):
        if not isinstance(body, dict) or set(body) - {'enabled', 'paused', 'interval', 'retry'}:
            raise ValueError('预览任务选项无效。')
        for key in ('enabled', 'paused', 'retry'):
            if key in body and type(body[key]) is not bool:
                raise ValueError('预览任务选项无效。')
        if 'interval' in body and (type(body['interval']) is not int or not 30 <= body['interval'] <= 3600):
            raise ValueError('两次预览至少间隔 30 秒。')
        with self.lock, self.connect() as c:
            self._preview_config = {**self._preview_config, **{k: v for k, v in body.items() if k != 'retry'}}
            self._preview_generation += 1
            stamp = time.time()
            c.execute("UPDATE capture_jobs SET status='pending',lease='',lease_until=0,next_at=?,attempts=max(0,attempts-1) WHERE kind='preview' AND status='running'", (stamp,))
            if not self._preview_config['enabled']:
                c.execute("UPDATE capture_jobs SET status='skipped',lease='',lease_until=0,error_code='disabled',error='网站预览已关闭。',updated_at=? WHERE kind='preview' AND status IN ('pending','running','retry')", (stamp,))
            else:
                for row in c.execute("SELECT j.id,r.payload FROM capture_jobs j JOIN resources r ON r.id=j.resource_id WHERE j.kind='preview' AND j.error_code='disabled' AND r.deleted=0 AND j.url=json_extract(r.payload,'$.url')").fetchall():
                    item = json.loads(row['payload'])
                    if not item['coverId'] and not item['thumbnail']:
                        c.execute("UPDATE capture_jobs SET status='pending',attempts=0,error='',error_code='',next_at=?,expected_revision=? WHERE id=?", (stamp, item['updatedAt'], row['id']))
            if body.get('retry'):
                for row in c.execute("SELECT j.id,r.payload FROM capture_jobs j JOIN resources r ON r.id=j.resource_id WHERE j.kind='preview' AND j.status IN ('retry','failed','skipped') AND r.deleted=0 AND j.url=json_extract(r.payload,'$.url')").fetchall():
                    item = json.loads(row['payload'])
                    if not item['coverId'] and not item['thumbnail']:
                        c.execute("UPDATE capture_jobs SET status='pending',attempts=0,error='',error_code='',next_at=?,expected_revision=? WHERE id=?", (stamp, item['updatedAt'], row['id']))
            c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', ('websitePreviews', json.dumps(self._preview_config)))
            self.dirty = True
        return self.preview_status()

    def preview_step(self):
        cfg = self._preview_config
        if not cfg['enabled'] or cfg['paused'] or time.monotonic() < self._preview_next:
            return False
        self._queue_legacy_previews()
        return self.capture_step('preview')

    def start_preview_worker(self):
        self.start_capture_worker()

    def stop_preview_worker(self):
        self.stop_capture_worker()
