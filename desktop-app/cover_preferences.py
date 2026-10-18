"""Atomic field-guarded cover preferences using existing resource/attachment storage."""
import base64
import binascii
import hashlib
import json

from cover_config import normalize_config
from edits import EditConflict


def _upload(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'name', 'mime', 'base64'}:
        raise ValueError('封面上传格式不正确。')
    from storage import text
    from capture_images import validate_image
    name = text(value['name'], 240, '图片名称', True)
    mime = text(value['mime'], 80, '图片类型', True)
    encoded = value['base64']
    if not isinstance(encoded, str) or len(encoded) > 4 * ((5 * 1024 * 1024 + 2) // 3):
        raise ValueError('封面图片超过 5 MB。')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('封面图片未完整上传，请重试。') from exc
    validate_image(raw, mime)
    return raw, name, hashlib.sha256(raw).hexdigest()


class CoverOperations:
    def update_cover(self, rid, body):
        from storage import identifier, text, validate
        rid = identifier(rid)
        if (not isinstance(body, dict) or
                not {'config', 'coverId', 'expected'} <= set(body) or
                not set(body) <= {'config', 'coverId', 'expected', 'upload'}):
            raise ValueError('封面保存选项无效。')
        expected = body['expected']
        if not isinstance(expected, dict) or set(expected) != {'coverConfig', 'coverId'}:
            raise ValueError('封面原值无效。')
        config = normalize_config(body['config'])
        baseline = normalize_config(expected['coverConfig'])
        cover_id = text(body['coverId'], 80, '封面 ID')
        old_id = text(expected['coverId'], 80, '封面原 ID')
        if cover_id:
            identifier(cover_id)
        if old_id:
            identifier(old_id)
        # Structural image validation and hashing never hold the Store's global lock.
        upload = _upload(body.get('upload'))
        written = []
        with self.lock:
            previous_dirty = self.dirty
            try:
                with self.connect() as c:
                    current = self._get(c, rid, True)
                    current_config = normalize_config(current.get('coverConfig'))
                    desired_id = cover_id
                    if upload:
                        raw, name, digest = upload
                        desired_id = None
                        # Bytes, not filenames, identify the existing image. Retry after
                        # a committed-but-lost response reuses the original attachment.
                        for attachment in current['attachments']:
                            if attachment['sha256'] != digest or attachment['size'] != len(raw):
                                continue
                            path = self.files / attachment['id']
                            try:
                                intact = not path.is_symlink() and path.read_bytes() == raw
                            except OSError:
                                intact = False
                            if intact:
                                desired_id = attachment['id']
                                break
                    conflicts = []
                    for field, old, desired, before in (
                        ('coverConfig', current_config, config, baseline),
                        ('coverId', current['coverId'], desired_id, old_id),
                    ):
                        if old != desired and old != before:
                            conflicts.append({'field': field, 'current': old, 'value': desired})
                    if conflicts:
                        raise EditConflict(current, conflicts)
                    if (current_config and current_config.get('version', 1) > 1 and
                            config is not None and config != current_config):
                        raise ValueError('该封面由更新版本创建。请更新应用，或明确恢复自动封面。')
                    if current_config == config and current['coverId'] == desired_id:
                        return {'resource': current, 'changed': False}
                    if upload and desired_id is None:
                        result = self.attach_in_transaction(c, rid, raw, {'name': name}, written)
                        desired_id = result['attachment']['id']
                    desired = validate({'coverConfig': config, 'coverId': desired_id}, current)
                    if desired_id and desired_id != current['coverId']:
                        row = c.execute('SELECT resource_id,payload,deleted FROM attachments WHERE id=?', (desired_id,)).fetchone()
                        if not row or row['resource_id'] != rid or row['deleted']:
                            raise ValueError('封面图片不存在。')
                        image = json.loads(row['payload'])
                        if not image['mime'].startswith('image/'):
                            raise ValueError('封面需要图片附件。')
                        desired['colors'] = image['colors']
                    self._write(c, desired, current)
                    return {'resource': self._get(c, rid, True), 'changed': True}
            except Exception:
                for destination in written:
                    destination.unlink(missing_ok=True)
                self.dirty = previous_dirty
                raise
