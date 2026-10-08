"""Explicit, reversible sharing of already stored duplicate attachment bytes."""
import copy
import json
import os
import re
import shutil
import stat
import tempfile
import threading
import uuid
from pathlib import Path

class SharingCancelled(Exception):
    pass

def identity(path):
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode):raise ValueError('附件不是普通文件，请重新检查。')
    return info.st_dev,info.st_ino

def unique_bytes(store,attachments):
    found={}
    for attachment in attachments:
        path=store.files/attachment['id']
        try:
            key=identity(path);found[key]=path.stat().st_size
        except (OSError,ValueError):pass
    return sum(found.values())

def start_sharing(store,body):
    if not isinstance(body,dict):raise ValueError('复用选项无效。')
    if body.get('cancel') is True:
        if set(body)!={'cancel','jobId'} or not isinstance(body['jobId'],str):raise ValueError('取消选项无效。')
        with store.health_lock:
            current=store.sharing_state
            if body['jobId']!=current['jobId']:raise ValueError('复用任务已变化，请刷新状态。')
            if current['status']=='running' and current.get('phase')!='cleanup':store.share_cancel.set();current['cancelRequested']=True
        return store.health_status()
    if set(body)!={'scanJobId','sha256'} or not isinstance(body.get('scanJobId'),str) or not isinstance(body.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',body['sha256']):raise ValueError('请从最新检查结果选择相同内容组。')
    # Busy checks need no storage lock, so they remain responsive during a job.
    with store.health_lock:
        if store.sharing_state['status']=='running':raise ValueError('正在复用另一组文件，请等完成后再操作。')
        if store.health_state['status']=='running':raise ValueError('附件检查仍在运行，请等完成后再操作。')
    with store.lock,store.health_lock:
        if store.sharing_state['status']=='running' or store.health_state['status']=='running':raise ValueError('附件任务仍在运行，请稍后重试。')
        report=store.health_state['report']
        if store.health_state['status']!='complete' or not report or body['scanJobId']!=store.health_state['jobId'] or store._health_catalog()[2]!=report['signature']:raise ValueError('检查结果已变化，请重新检查附件。')
        group=next((g for g in report['duplicates'] if g['sha256']==body['sha256']),None)
        if not group:raise ValueError('当前检查中没有这组相同附件。')
        if group.get('storedCopies')==1:raise ValueError('这组附件已经复用相同文件内容。')
        plan={'items':copy.deepcopy(group['items']),'signature':report['signature']}
        store.share_cancel.clear()
        store.sharing_state={'status':'running','jobId':str(uuid.uuid4()),'phase':'checking','progress':{'done':0,'total':len(group['items'])},'cancelRequested':False,'backup':None}
        threading.Thread(target=run_sharing,args=(store,plan),daemon=True).start()
    return store.health_status()

def run_sharing(store,plan):
    # Keep the library lock through rollback; queued writes/backups cannot interleave.
    with store.lock:_run_sharing_locked(store,plan)

def _run_sharing_locked(store,plan):
    from backups import file_matches
    from storage import identifier
    stage=None;published=[];backup=None
    def check_cancel():
        if store.share_cancel.is_set():raise SharingCancelled()
    def progress(phase,done,total):
        with store.health_lock:store.sharing_state.update(phase=phase,progress={'done':done,'total':total})
    def verify(path,attachment):
        check_cancel();identity(path)
        if not file_matches(path,attachment):raise ValueError('文件内容已变化，请重新检查后重试。')
    try:
        catalog=store._health_catalog()
        if catalog[2]!=plan['signature']:raise ValueError('检查结果已变化，请重新检查附件。')
        items=plan['items'];source=store.files/identifier(items[0]['id']);paths=[store.files/identifier(a['id']) for a in items]
        for i,(path,a) in enumerate(zip(paths,items)):
            verify(path,a);progress('checking',i+1,len(items))
        source_index=max(range(len(paths)),key=lambda i:paths[i].stat().st_nlink)
        source=paths[source_index];reference=items[source_index]
        source_identity=identity(source)
        changes=[(path,a) for path,a in zip(paths,items) if identity(path)!=source_identity]
        if not changes:
            with store.health_lock:store.sharing_state.update(status='complete',changedFiles=0,sharedBytes=0,cancelRequested=False)
            return
        before=unique_bytes(store,catalog[1]);check_cancel();progress('backup',0,1)
        backup=store.create_backup(allow_missing=True)
        with store.health_lock:store.sharing_state['backup']=backup
        check_cancel();stage=Path(tempfile.mkdtemp(prefix='.share-',dir=store.files))
        (stage/'manifest.json').write_text(json.dumps({'format':'shiji-sharing-rollback','backup':backup['name'],'sha256':items[0]['sha256'],'ids':[a['id'] for _,a in changes]}),encoding='utf-8')
        prepared=[]
        for i,(path,a) in enumerate(changes):
            check_cancel();old=stage/(a['id']+'.old');new=stage/(a['id']+'.new')
            try:
                os.link(path,old,follow_symlinks=False);os.link(source,new,follow_symlinks=False)
            except (OSError,NotImplementedError,AttributeError,TypeError):raise ValueError('无法建立文件复用。请确认文件系统支持硬链接，且数据目录可写。')
            verify(old,a);verify(new,a)
            if identity(path)!=identity(old) or identity(new)!=source_identity:raise ValueError('文件路径已变化，请重新检查后重试。')
            prepared.append((path,old,new));progress('preparing',i+1,len(changes))
        verify(source,reference)
        if identity(source)!=source_identity:raise ValueError('来源文件已变化，请重新检查后重试。')
        for i,(path,old,new) in enumerate(prepared):
            check_cancel()
            if identity(path)!=identity(old):raise ValueError('文件路径已变化，请重新检查后重试。')
            # Track before replace: even a replace that raises after writing can roll back.
            published.append((path,old));os.replace(new,path);progress('publishing',i+1,len(changes))
        verify(source,reference)
        if any(identity(path)!=source_identity for path in paths):raise ValueError('复用校验未通过，请重新检查后重试。')
        check_cancel();after=unique_bytes(store,catalog[1])
        # Commit while cancellation is serialized. Removing old links is irreversible;
        # after this boundary only cleanup remains, so late cancellation cannot roll back.
        with store.health_lock:
            check_cancel();store.sharing_state.update(phase='cleanup',cancelRequested=False)
        cleanup_warning=None
        try:
            shutil.rmtree(stage);stage=None
        except Exception:
            cleanup_warning='文件内容已复用，但临时文件未完全清理。它们可能仍占空间；请保留暂存目录并核对恢复前快照。'
        with store.health_lock:
            store.sharing_state.update(status='complete',changedFiles=len(changes),sharedBytes=max(0,before-after),cancelRequested=False)
            if cleanup_warning:
                store.sharing_state['cleanupWarning']=cleanup_warning
                if stage.exists():store.sharing_state['recoveryDirectory']=stage.name
    except Exception as error:
        rollback_failed=[]
        # Every changed path still contains verified identical bytes; original inodes
        # are retained in the stage directory if filesystem rollback cannot finish.
        with store.lock:
            for path,old in reversed(published):
                try:os.replace(old,path)
                except OSError:rollback_failed.append(path.name)
            if stage and not rollback_failed:
                try:shutil.rmtree(stage);stage=None
                except OSError:rollback_failed.append('cleanup')
        cancelled=isinstance(error,SharingCancelled) and not rollback_failed
        message=str(error) if isinstance(error,ValueError) else '复用未完成，请确认数据目录可读写，再重新检查。'
        if rollback_failed:message='部分文件未能回退或临时文件未清理。请保留暂存目录，并核对恢复前快照。'
        with store.health_lock:
            store.sharing_state.update(status='cancelled' if cancelled else 'failed',error=message,cancelRequested=False,changedFiles=0,sharedBytes=0)
            if stage:store.sharing_state.update(recoveryDirectory=stage.name,rollbackFailures=rollback_failed)
