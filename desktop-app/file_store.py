"""Keep attachment identities separate while sharing verified immutable bytes.

Only new publications participate. Existing files are never rewritten in place;
repair replaces a path, so other hard-linked attachments keep their own bytes.
"""
import json
import os

def publish_file(store,connection,attachment,raw=None,staged=None):
    """Atomically publish one attachment, falling back when linking is unavailable.

    Caller owns the database transaction and must unlink the published path if
    that transaction fails. Candidate files include recoverable trash records.
    """
    from backups import file_matches
    from storage import identifier
    aid=identifier(attachment['id']);destination=store.files/aid
    temporary=store.files/(aid+'.tmp');shared=False
    if destination.exists() or destination.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise ValueError('附件存储冲突，未覆盖已有文件。')
    try:
        for row in connection.execute('SELECT payload FROM attachments ORDER BY rowid'):
            candidate=json.loads(row['payload'])
            if candidate.get('sha256')!=attachment['sha256'] or candidate.get('size')!=attachment['size']:continue
            try:source=store.files/identifier(candidate['id'])
            except (KeyError,ValueError):continue
            if source==destination or not file_matches(source,attachment):continue
            try:
                os.link(source,temporary,follow_symlinks=False)
                # Recheck the new path: the candidate may have changed during linking.
                if file_matches(temporary,attachment):shared=True;break
            except (OSError,NotImplementedError,AttributeError,TypeError):pass
            temporary.unlink(missing_ok=True)
        if not shared:
            if raw is not None:temporary.write_bytes(raw)
            elif staged is not None:os.replace(staged,temporary)
            else:raise ValueError('No attachment bytes supplied')
        os.replace(temporary,destination)
        return shared
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
