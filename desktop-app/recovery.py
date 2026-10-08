"""Short lived, single-use recovery receipts; no persistent schema changes."""
import io
import json
import re
import secrets
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

class RecoveryOperations:
    def _recovery_state(self):
        if not hasattr(self,'_undo_receipts'):self._undo_receipts={};self._restore_tickets={}
    def cleanup_restore_staging(self):
        # Leases survive restart. Active validation/apply is never reaped.
        with self.lock:
            self._recovery_state();protected={str(entry[2]) for entry in self._restore_tickets.values() if entry[1] is None or entry[3] or entry[0]>time.monotonic()}
            expired=[]
            for token,(expiry,plan,directory,busy) in list(self._restore_tickets.items()):
                if expiry<=time.monotonic() and plan is not None and not busy:
                    self._restore_tickets.pop(token,None);expired.append(directory)
        for directory in self.root.glob('restore-preview-*'):
            if directory.is_symlink() or not directory.is_dir() or str(directory) in protected:continue
            try:
                lease=directory/'.expires'
                deadline=float(lease.read_text()) if lease.is_file() else directory.stat().st_mtime+600
                if deadline<=time.time():expired.append(directory)
            except (OSError,ValueError):continue
        for directory in set(expired):shutil.rmtree(directory,ignore_errors=True)
    def _receipt(self,kind,payload):
        self._recovery_state()
        self._undo_receipts={k:v for k,v in self._undo_receipts.items() if v[0]>time.monotonic()}
        token=secrets.token_urlsafe(24);self._undo_receipts[token]=(time.monotonic()+15,kind,payload)
        return {'undoToken':token,'undoSeconds':15}
    def invalidate_trash_undo(self,ids):
        self._recovery_state()
        for token,(_,kind,payload) in list(self._undo_receipts.items()):
            if kind=='trash' and set(ids).intersection(payload):self._undo_receipts.pop(token,None)
    def undo(self,token):
        with self.lock:
            self._recovery_state();entry=self._undo_receipts.get(token)
            if not entry or entry[0]<=time.monotonic():raise ValueError('撤销已过期，请到回收站恢复资源。')
            _,kind,payload=entry
            with self.connect() as c:
                if kind=='trash':
                    # Undo only membership; never overwrite edits made meanwhile.
                    for rid in payload:
                        if not c.execute('SELECT 1 FROM resources WHERE id=? AND deleted=1',(rid,)).fetchone():raise ValueError('资源状态已改变，请到回收站检查。')
                    for rid in payload:c.execute('UPDATE resources SET deleted=0 WHERE id=?',(rid,))
                else:
                    if c.execute('SELECT 1 FROM smart_collections WHERE id=? OR name=?',(payload[0],payload[1])).fetchone():raise ValueError('同名集合已存在，请先检查集合。')
                    c.execute('INSERT INTO smart_collections VALUES(?,?,?)',payload)
            self._undo_receipts.pop(token);self.dirty=True
            return {'ok':True}
    def _expire_restores(self):
        self._recovery_state()
        for key,(expiry,plan,directory,busy) in list(self._restore_tickets.items()):
            if expiry<=time.monotonic() and plan is not None and not busy:shutil.rmtree(directory,ignore_errors=True);self._restore_tickets.pop(key,None)
    def preflight_restore(self,source):
        # The lock bounds tickets, not archive validation or attachment copying.
        with self.lock:
            self._expire_restores()
            if len(self._restore_tickets)>=2:raise ValueError('已有备份等待确认，请先取消或完成恢复。')
            token=secrets.token_urlsafe(24);directory=Path(tempfile.mkdtemp(prefix='restore-preview-',dir=self.root))
            (directory/'.expires').write_text(str(time.time()+600))
            self._restore_tickets[token]=(time.monotonic()+600,None,directory,False)
        try:
            from backups import MAX_ARCHIVE
            if isinstance(source,(bytes,bytearray)):
                if len(source)>MAX_ARCHIVE:raise ValueError('完整备份超过 16 GB。')
                source=io.BytesIO(source)
            else:
                source=Path(source)
                if source.stat().st_size>MAX_ARCHIVE:raise ValueError('完整备份超过 16 GB。')
            with zipfile.ZipFile(source) as archive:plan=self._validate_archive(archive,directory)
            items,files,collections,meta,smart=plan
            summary={'resources':len(items),'active':sum(not i['deleted'] for i in items),'trash':sum(i['deleted'] for i in items),'attachments':len(files),'bytes':sum(a['size'] for a in files),'collections':len(collections),'smartCollections':len(smart)}
            with self.lock:
                (directory/'.expires').write_text(str(time.time()+600))
                self._restore_tickets[token]=(time.monotonic()+600,plan,directory,False)
            return {'ticket':token,'expiresIn':600,'summary':summary}
        except Exception as e:
            with self.lock:self._restore_tickets.pop(token,None)
            shutil.rmtree(directory,ignore_errors=True)
            if isinstance(e,(zipfile.BadZipFile,KeyError,TypeError,AttributeError,json.JSONDecodeError,UnicodeDecodeError,RuntimeError)):raise ValueError('备份格式不正确或文件不完整。') from e
            raise
    def cancel_restore(self,token):
        with self.lock:
            self._expire_restores();entry=self._restore_tickets.get(token)
            if entry and entry[3]:raise ValueError('恢复已开始，请等待完成。')
            self._restore_tickets.pop(token,None)
        if entry:shutil.rmtree(entry[2],ignore_errors=True)
        return {'ok':True}
    def confirm_restore(self,body):
        if body.get('confirm') is not True:raise ValueError('请先检查摘要并确认恢复。')
        token=body.get('ticket')
        with self.lock:
            self._expire_restores();entry=self._restore_tickets.get(token)
            if not entry or entry[1] is None or entry[3]:raise ValueError('备份预检已过期或正在恢复，请重新选择。')
            expiry,plan,directory,_=entry;self._restore_tickets[token]=(expiry,plan,directory,True)
        try:return self._apply_archive(plan,directory)
        finally:
            with self.lock:self._restore_tickets.pop(token,None)
            shutil.rmtree(directory,ignore_errors=True)
    def preflight_backup(self,name):
        # Pin complete ZIPs against retention; snapshots use the same ZIP validator.
        with self._backup_lock:
            if re.fullmatch(r'shiji-[0-9-]+\.zip',name):
                with tempfile.TemporaryDirectory(dir=self.root,prefix='backup-pin-') as tmp:
                    source=Path(tmp)/'backup.zip';shutil.copyfile(self.backup_file(name),source)
                    return self.preflight_restore(source)
            if not re.fullmatch(r'auto-[0-9-]+-[a-f0-9]{8}',name):raise ValueError('备份不存在。')
            snapshot=self.backups/name
            if snapshot.is_symlink() or not snapshot.is_dir():raise ValueError('备份不存在。')
            manifest=json.loads((snapshot/'manifest.json').read_text())
            with tempfile.TemporaryDirectory(dir=self.root,prefix='snapshot-pin-') as tmp:
                source=Path(tmp)/'backup.zip'
                with zipfile.ZipFile(source,'w',compression=zipfile.ZIP_STORED) as archive:
                    archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
                    for a in manifest['attachments']:
                        if not re.fullmatch(r'[a-f0-9]{64}',a.get('sha256','')) or not re.fullmatch(r'[a-f0-9-]{36}',a.get('id','')):raise ValueError('备份附件无效。')
                        obj=self.backups/'objects'/a['sha256']
                        if obj.is_symlink():raise ValueError('备份附件无效。')
                        archive.write(obj,'files/'+a['id'])
                return self.preflight_restore(source)
