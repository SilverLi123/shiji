"""Local derived tasks; one scheduler, durable leases, no network under Store locks."""
import json
import threading
import time
import uuid
import hashlib

ACTIVE = ('pending', 'running', 'retry')
MAX_ATTEMPTS = 3
LEASE_SECONDS = 120


class CaptureFailure(Exception):
    def __init__(self, code, message, retryable=True):
        super().__init__(message)
        self.code, self.message, self.retryable = code, message, retryable


def fetch_payload(item, kind, options=None):
    from capture import capture_payload, capture_image, website_preview
    from capture_images import validate_image
    from capture_rules import suggest
    if kind == 'asset':
        try:
            return {'metadata': {}, 'image': capture_image(options['url'])}
        except CaptureFailure:
            raise
        except ValueError as e:
            raise CaptureFailure('blocked', '图片地址未通过公网安全校验。', False) from e
        except Exception as e:
            raise CaptureFailure('image-network', '网页图片暂时无法保存，原收藏已保留。') from e
    if kind == 'preview':
        raw, source, method = website_preview(item['url'])
        from storage import detect_mime
        try:
            validate_image(raw, detect_mime(raw))
        except ValueError as e:
            raise CaptureFailure('image-invalid', '图片文件无法验证，已保留海报。', False) from e
        return {'metadata': {}, 'image': (raw, source, method)}
    result = capture_payload(item['url'], item['thumbnail'], not bool(item['coverId']))
    result['suggestions'] = suggest(item, result['metadata'])
    return result


class CaptureOperations:
    def init_capture_jobs(self, c):
        c.executescript('''
          CREATE TABLE IF NOT EXISTS capture_jobs(
            id TEXT PRIMARY KEY,resource_id TEXT NOT NULL,kind TEXT NOT NULL,
            url TEXT NOT NULL,resource_version TEXT NOT NULL,expected_revision TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,
            next_at REAL NOT NULL,error_code TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT '',
            created_at REAL NOT NULL,updated_at REAL NOT NULL,lease TEXT NOT NULL DEFAULT '',
            lease_until REAL NOT NULL DEFAULT 0,suggestions TEXT NOT NULL DEFAULT '{}',
            suggestion_state TEXT NOT NULL DEFAULT 'pending',options TEXT NOT NULL DEFAULT '{}',
            options_key TEXT NOT NULL DEFAULT '',
            UNIQUE(resource_id,url,kind,resource_version,options_key));
          CREATE INDEX IF NOT EXISTS capture_due ON capture_jobs(status,next_at,created_at);
          CREATE INDEX IF NOT EXISTS capture_resource ON capture_jobs(resource_id,kind);
          CREATE TABLE IF NOT EXISTS capture_control(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        c.execute('INSERT OR IGNORE INTO capture_control VALUES(?,?)', ('engine', json.dumps({'paused': False, 'generation': 0})))
        self._capture_stop = threading.Event()
        self._capture_step_lock = threading.Lock()
        self._capture_active = None
        self._capture_next = 0
        self._recover_capture(c)

    def _recover_capture(self, c):
        stamp = time.time()
        c.execute("UPDATE capture_jobs SET status=CASE WHEN attempts>=? THEN 'failed' ELSE 'retry' END,lease='',lease_until=0,next_at=?,updated_at=?,error_code='interrupted',error='上次处理已中断，可继续或重试。' WHERE status='running' AND lease_until<=?", (MAX_ATTEMPTS, stamp, stamp, stamp))

    def enqueue_capture(self, c, item, kind='capture', options=None):
        if item.get('kind') != 'website' or item.get('deleted') or not item.get('url'):
            return None
        stamp = time.time()
        options_json = json.dumps(options or {}, sort_keys=True)
        key = hashlib.sha256(options_json.encode()).hexdigest() if options else ''
        c.execute('INSERT OR IGNORE INTO capture_jobs(id,resource_id,kind,url,resource_version,expected_revision,next_at,created_at,updated_at,options,options_key) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                  (str(uuid.uuid4()), item['id'], kind, item['url'], item['updatedAt'], item['updatedAt'], stamp, stamp, stamp, options_json, key))
        return c.execute('SELECT * FROM capture_jobs WHERE resource_id=? AND url=? AND kind=? AND resource_version=? AND options_key=?', (item['id'], item['url'], kind, item['updatedAt'], key)).fetchone()

    @staticmethod
    def _task(row):
        return {'id': row['id'], 'resourceId': row['resource_id'], 'type': row['kind'],
                'url': row['url'], 'resourceVersion': row['resource_version'],
                'expectedRevision': row['expected_revision'], 'status': row['status'],
                'attempts': row['attempts'], 'nextAt': row['next_at'],
                'errorCode': row['error_code'], 'error': row['error'],
                'createdAt': row['created_at'], 'updatedAt': row['updated_at'],
                'suggestions': json.loads(row['suggestions']), 'suggestionState': row['suggestion_state'],
                'title': row['title'] if 'title' in row.keys() else ''}

    def capture_status(self, limit=30):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('任务列表数量无效。')
        with self.lock, self.connect() as c:
            self._recover_capture(c)
            control = json.loads(c.execute("SELECT value FROM capture_control WHERE key='engine'").fetchone()[0])
            counts = {key: 0 for key in (*ACTIVE, 'completed', 'failed', 'cancelled', 'skipped')}
            counts.update({r[0]: r[1] for r in c.execute('SELECT status,count(*) FROM capture_jobs GROUP BY status')})
            rows = c.execute("SELECT j.*,json_extract(r.payload,'$.title') AS title FROM capture_jobs j LEFT JOIN resources r ON r.id=j.resource_id ORDER BY j.updated_at DESC,j.id LIMIT ?", (limit,)).fetchall()
            return {'paused': control['paused'], 'counts': counts, 'tasks': [self._task(r) for r in rows],
                    'active': sum(counts[s] for s in ACTIVE), 'maxAttempts': MAX_ATTEMPTS}

    def request_capture(self, rid, body):
        from storage import identifier, normalize_url
        if not isinstance(body, dict) or set(body) != {'url', 'updatedAt'}:
            raise ValueError('网页补全选项无效。')
        rid = identifier(rid)
        url = normalize_url(body['url'])
        with self.lock, self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            item = self._get(c, rid, True)
            if item['url'] != url or item['updatedAt'] != body['updatedAt']:
                return {'status': 'skipped', 'resource': item}
            row = self.enqueue_capture(c, item)
            return {'status': row['status'] if row else 'skipped', 'resource': item, 'task': self._task(row) if row else None}

    def capture_action(self, body):
        from storage import identifier
        if not isinstance(body, dict) or set(body) - {'action', 'id', 'updatedAt'}:
            raise ValueError('后台任务选项无效。')
        action = body.get('action')
        if action not in ('pause', 'resume', 'retry', 'cancel', 'accept', 'ignore'):
            raise ValueError('后台任务操作无效。')
        with self.lock, self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            stamp = time.time()
            if action in ('pause', 'resume'):
                control = json.loads(c.execute("SELECT value FROM capture_control WHERE key='engine'").fetchone()[0])
                control.update(paused=action == 'pause', generation=control['generation'] + 1)
                c.execute("UPDATE capture_control SET value=? WHERE key='engine'", (json.dumps(control),))
                if action == 'pause':
                    c.execute("UPDATE capture_jobs SET status='pending',lease='',lease_until=0,attempts=max(0,attempts-1),next_at=?,updated_at=? WHERE status='running'", (stamp, stamp))
            else:
                tid = identifier(body.get('id', ''), '任务 ID')
                row = c.execute('SELECT * FROM capture_jobs WHERE id=?', (tid,)).fetchone()
                if not row:
                    raise ValueError('任务已不存在。')
                if action == 'cancel':
                    c.execute("UPDATE capture_jobs SET status='cancelled',lease='',lease_until=0,updated_at=? WHERE id=? AND status IN ('pending','running','retry')", (stamp, tid))
                elif action == 'retry':
                    if row['status'] in ACTIVE:
                        raise ValueError('任务正在处理，无需重复提交。')
                    item = self._get(c, row['resource_id'], True)
                    if item['url'] != row['url']:
                        raise ValueError('网址已修改，请处理新网址的任务。')
                    c.execute("UPDATE capture_jobs SET status='pending',attempts=0,next_at=?,updated_at=?,expected_revision=?,lease='',lease_until=0,error_code='',error='' WHERE id=?", (stamp, stamp, item['updatedAt'], tid))
                else:
                    self._review_capture(c, row, body, stamp)
        return self.capture_status()

    def _review_capture(self, c, row, body, stamp):
        item = self._get(c, row['resource_id'], True)
        if item['updatedAt'] != body.get('updatedAt') or item['updatedAt'] != row['expected_revision'] or item['url'] != row['url']:
            raise ValueError('资源刚刚变化，请刷新后查看最新建议。')
        if row['suggestion_state'] != 'pending' or row['status'] in ('pending', 'running', 'cancelled', 'skipped'):
            raise ValueError('没有可处理的新建议。')
        if body['action'] == 'accept':
            suggestion = json.loads(row['suggestions'])
            changes = {}
            if item['category'] == '其他' and suggestion.get('category'):
                changes['category'] = suggestion['category']
            if suggestion.get('tags'):
                changes['tags'] = list(dict.fromkeys(item['tags'] + suggestion['tags']))[:30]
            if changes:
                item = self._write(c, changes, item)
        c.execute('UPDATE capture_jobs SET suggestion_state=?,expected_revision=?,updated_at=? WHERE id=?', ('accepted' if body['action'] == 'accept' else 'ignored', item['updatedAt'], stamp, row['id']))

    def _claim_capture(self, kind):
        with self.lock, self.connect() as c:
            if self._capture_stop.is_set():
                return None
            c.execute('BEGIN IMMEDIATE')
            self._recover_capture(c)
            control = json.loads(c.execute("SELECT value FROM capture_control WHERE key='engine'").fetchone()[0])
            if control['paused']:
                return None
            stamp = time.time()
            query = "SELECT * FROM capture_jobs WHERE status IN ('pending','retry') AND next_at<=? AND NOT EXISTS(SELECT 1 FROM capture_jobs busy WHERE busy.resource_id=capture_jobs.resource_id AND busy.status='running' AND busy.lease_until>?)"
            params = [stamp, stamp]
            if kind:
                query += ' AND kind=?'
                params.append(kind)
            else:
                # Legacy previews require explicit opt-in and their own rate gate.
                if not self._preview_config['enabled'] or self._preview_config['paused'] or time.monotonic() < self._preview_next:
                    query += " AND kind!='preview'"
            row = c.execute(query + ' ORDER BY created_at,id LIMIT 1', params).fetchone()
            if not row:
                return None
            try:
                item = self._get(c, row['resource_id'], True)
            except ValueError:
                item = None
            if not item or item['kind'] != 'website' or item['url'] != row['url'] or item['updatedAt'] != row['expected_revision']:
                c.execute("UPDATE capture_jobs SET status='skipped',error_code='changed',error='资源已修改或移入回收站，保留当前内容。',updated_at=? WHERE id=?", (stamp, row['id']))
                return None
            if row['kind'] == 'preview' and (item['coverId'] or item['thumbnail']):
                c.execute("UPDATE capture_jobs SET status='skipped',updated_at=? WHERE id=?", (stamp, row['id']))
                return None
            lease = str(uuid.uuid4())
            c.execute("UPDATE capture_jobs SET status='running',attempts=attempts+1,lease=?,lease_until=?,updated_at=? WHERE id=?", (lease, stamp + LEASE_SECONDS, stamp, row['id']))
            job = dict(row, lease=lease, lease_until=stamp + LEASE_SECONDS, attempts=row['attempts'] + 1)
            self._capture_active = (job['id'], lease)
            if row['kind'] == 'preview':
                self._preview_next = time.monotonic() + self._preview_config['interval']
            return job, item, control['generation'], self._preview_generation

    def _owns_capture(self, c, job, generation, preview_generation):
        row = c.execute('SELECT * FROM capture_jobs WHERE id=?', (job['id'],)).fetchone()
        control = json.loads(c.execute("SELECT value FROM capture_control WHERE key='engine'").fetchone()[0])
        return row and row['status'] == 'running' and row['lease'] == job['lease'] and row['lease_until'] > time.time() and not control['paused'] and control['generation'] == generation and (job['kind'] != 'preview' or preview_generation == self._preview_generation)

    def _capture_failure(self, job, error, generation, preview_generation):
        with self.lock, self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if not self._owns_capture(c, job, generation, preview_generation):
                return
            try:
                current = self._get(c, job['resource_id'], True)
            except ValueError:
                current = None
            if not current or current['url'] != job['url'] or current['updatedAt'] != job['expected_revision']:
                c.execute("UPDATE capture_jobs SET status='skipped',lease='',lease_until=0,error_code='changed',error='资源已变化，保留当前内容。',updated_at=? WHERE id=?", (time.time(), job['id']))
                return
            retry = error.retryable and job['attempts'] < MAX_ATTEMPTS
            stamp = time.time()
            c.execute('UPDATE capture_jobs SET status=?,next_at=?,error_code=?,error=?,lease="",lease_until=0,updated_at=? WHERE id=?', ('retry' if retry else 'failed', stamp + min(300, 5 * 2 ** (job['attempts'] - 1)), error.code, error.message, stamp, job['id']))

    def capture_step(self, kind=None):
        if not self._capture_step_lock.acquire(False):
            return False
        try:
            claimed = self._claim_capture(kind)
            if not claimed:
                return False
            job, item, generation, preview_generation = claimed
            try:
                result = fetch_payload(item, job['kind'], json.loads(job['options']))
                if self._capture_stop.is_set():
                    return False
                return self._apply_capture(job, item, result, generation, preview_generation)
            except CaptureFailure as e:
                if not self._capture_stop.is_set():
                    self._capture_failure(job, e, generation, preview_generation)
            except Exception:
                if not self._capture_stop.is_set():
                    self._capture_failure(job, CaptureFailure('processing', '补全暂未完成，可稍后重试。'), generation, preview_generation)
            return False
        finally:
            self._capture_active = None
            self._capture_step_lock.release()

    def _apply_capture(self, job, original, result, generation, preview_generation):
        from quick_capture import fallback_title
        from storage import dump
        written = []
        with self.lock:
            previous_dirty = self.dirty
            try:
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    if not self._owns_capture(c, job, generation, preview_generation):
                        return False
                    try:
                        current = self._get(c, original['id'], True)
                    except ValueError:
                        current = None
                    if not current or current['url'] != job['url'] or current['updatedAt'] != job['expected_revision'] or current['attachments'] != original['attachments'] or current['coverId'] != original['coverId']:
                        c.execute("UPDATE capture_jobs SET status='skipped',lease='',lease_until=0,error_code='changed',error='资源已变化，保留当前内容。',updated_at=? WHERE id=?", (time.time(), job['id']))
                        return False
                    meta = result.get('metadata', {})
                    changes = {}
                    for key in ('title', 'description', 'favicon', 'sourceUrl'):
                        value = meta.get(key, '')
                        from urllib.parse import urlsplit
                        if isinstance(value, str) and value.strip() and (not current[key] or (key == 'title' and current[key] in (fallback_title(current['url']), current['url'], urlsplit(current['url']).hostname))):
                            changes[key] = value
                    if changes:
                        self._write(c, changes, current)
                        current = self._get(c, current['id'])
                    if result.get('image') and (not current['coverId'] or job['kind'] == 'asset'):
                        raw, source, method = result['image']
                        digest = hashlib.sha256(raw).hexdigest()
                        same = next((a for a in current['attachments'] if a['sha256'] == digest and not (self.files/a['id']).is_symlink() and (self.files/a['id']).is_file() and (self.files/a['id']).read_bytes() == raw), None)
                        if same:
                            if not current['coverId']:
                                self._write(c, {'coverId': same['id']}, current)
                        else:
                            self.attach_in_transaction(c, current['id'], raw, {'name': '网页图片' if job['kind'] == 'asset' else ('网站预览.png' if method == 'Chrome 截图' else '网站预览图'), 'cover': not bool(current['coverId']), 'sourceUrl': source, 'license': '待确认'}, written)
                        current = self._get(c, current['id'])
                    cover_error = result.get('coverError')
                    retry = bool(cover_error) and cover_error.get('retryable', True) and job['attempts'] < MAX_ATTEMPTS
                    status = ('retry' if retry else 'failed') if cover_error else 'completed'
                    stamp = time.time()
                    # Only revisions created by this fenced transaction may advance
                    # sibling tasks. A user edit never enters this branch.
                    c.execute('UPDATE capture_jobs SET expected_revision=? WHERE resource_id=? AND url=? AND expected_revision=?', (current['updatedAt'], current['id'], current['url'], original['updatedAt']))
                    c.execute('UPDATE capture_jobs SET status=?,expected_revision=?,suggestions=?,next_at=?,error_code=?,error=?,lease="",lease_until=0,updated_at=? WHERE id=?', (status, current['updatedAt'], dump(result.get('suggestions', {})), stamp + (5 * 2 ** (job['attempts'] - 1) if retry else 0), 'cover' if cover_error else '', '真实封面暂不可用，已保留海报和收藏。' if cover_error else '', stamp, job['id']))
                return status == 'completed'
            except Exception:
                for path in written:
                    path.unlink(missing_ok=True)
                self.dirty = previous_dirty
                raise

    def start_capture_worker(self):
        if getattr(self, '_capture_worker', None) and self._capture_worker.is_alive():
            return
        self._capture_stop.clear()
        def run():
            while not self._capture_stop.wait(.5):
                try:
                    self.cleanup_restore_staging()
                    self._queue_legacy_previews()
                    self.capture_step()
                except Exception:
                    # Do not log URLs, resource contents, tokens or arbitrary remote errors.
                    continue
        self._capture_worker = threading.Thread(target=run, name='shiji-capture', daemon=True)
        self._capture_worker.start()

    def stop_capture_worker(self):
        self._capture_stop.set()
        with self.lock:
            active = self._capture_active
            if active:
                with self.connect() as c:
                    c.execute("UPDATE capture_jobs SET status='retry',lease='',lease_until=0,next_at=? WHERE id=? AND lease=? AND status='running'", (time.time(), *active))
        if getattr(self, '_capture_worker', None):
            self._capture_worker.join(timeout=2)
