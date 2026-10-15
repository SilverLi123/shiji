"""Local transport receipts; never exported as resource or sync content."""
import hashlib
import json
import time
import uuid


def request_identifier(value):
    if not isinstance(value, str):
        raise ValueError('收藏请求 ID 无效。')
    try:
        valid = str(uuid.UUID(value)) == value
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('收藏请求 ID 无效。')
    return value


def fingerprint(page, selection, screenshot, image_url):
    value = {'page': page, 'selection': selection, 'imageUrl': image_url,
             'screenshot': hashlib.sha256(screenshot).hexdigest() if screenshot else ''}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


class CaptureReceiptOperations:
    def init_capture_receipts(self, c):
        c.execute('''CREATE TABLE IF NOT EXISTS clip_receipts(
            request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
            resource_id TEXT NOT NULL, created_at REAL NOT NULL)''')

    def _clip_receipt(self, c, request_id, expected=None):
        row = c.execute('SELECT * FROM clip_receipts WHERE request_id=?', (request_id,)).fetchone()
        if row and expected is not None and row['payload_hash'] != expected:
            raise ValueError('同一次收藏的内容已改变，请核对待发送记录。')
        return {'requestId': request_id, 'status': 'saved' if row else 'not_found',
                **({'resourceId': row['resource_id']} if row else {})}

    def clip_status(self, body):
        if not isinstance(body, dict) or set(body) != {'requestId'}:
            raise ValueError('收藏回执选项无效。')
        request_id = request_identifier(body['requestId'])
        with self.lock, self.connect() as c:
            return self._clip_receipt(c, request_id)

    def _record_clip(self, c, request_id, payload_hash, resource_id):
        c.execute('INSERT INTO clip_receipts VALUES(?,?,?,?)',
                  (request_id, payload_hash, resource_id, time.time()))
        return self._clip_receipt(c, request_id)
