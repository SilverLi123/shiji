"""Read-only scans and explicit file sharing; attachment identities stay separate."""
import copy
import hashlib
import json
import threading
import uuid

class HealthOperations:
    def init_health(self):
        self.health_lock=threading.RLock();self.health_cancel=threading.Event();self.share_cancel=threading.Event()
        self.sharing_state={'status':'idle','jobId':'','phase':'','progress':{'done':0,'total':0}}
        self.health_state={'status':'idle','jobId':'','progress':{'done':0,'total':0},'report':None}

    def _health_catalog(self):
        with self.lock,self.connect() as c:
            resources=[dict(r) for r in c.execute('SELECT * FROM resources ORDER BY id')]
            rows=[dict(r) for r in c.execute('SELECT * FROM attachments ORDER BY id')]
        # File recovery can change bytes without changing a single database row.
        # Cheap lstat fingerprints invalidate reports without reading file content again.
        file_state=[]
        for row in rows:
            try:
                stat=(self.files/row['id']).lstat()
                file_state.append((row['id'],stat.st_mode,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns))
            except OSError:file_state.append((row['id'],'unavailable'))
        try:directory_stamp=self.files.stat().st_mtime_ns
        except OSError:directory_stamp=None
        signature=hashlib.sha256(json.dumps([resources,rows,file_state,directory_stamp],sort_keys=True).encode()).hexdigest()
        owners={r['id']:{'id':r['id'],'title':json.loads(r['payload'])['title'],'deleted':bool(r['deleted'])} for r in resources}
        files=[]
        for row in rows:
            a=json.loads(row['payload']);owner=owners.get(row['resource_id'])
            files.append({**a,'resourceId':row['resource_id'],'resourceTitle':owner['title'] if owner else '所属资源不存在','inTrash':bool(row['deleted']) or bool(owner and owner['deleted']),'unlinked':owner is None})
        return resources,files,signature

    def health_status(self):
        with self.health_lock:
            result=copy.deepcopy(self.health_state);result['sharing']=copy.deepcopy(self.sharing_state)
        if result['report']:
            signature=None
            # Polling must not wait behind a background operation's storage lock.
            acquired=False if result['sharing']['status']=='running' else self.lock.acquire(blocking=False)
            try:
                if acquired:signature=self._health_catalog()[2]
                # The worker may have started between the first snapshot and acquire.
                # Storage -> health is the same order used by writers.
                with self.health_lock:
                    result=copy.deepcopy(self.health_state);result['sharing']=copy.deepcopy(self.sharing_state)
                if result['report']:
                    result['report']['stale']=signature is None or result['sharing']['status']=='running' or signature!=result['report']['signature']
                    if signature is None and result['sharing']['status']!='running':result['report']['staleReason']='busy'
                    result['report'].pop('signature',None)
            finally:
                if acquired:self.lock.release()
        return result

    def start_health(self,cancel=False):
        if not isinstance(cancel,bool):raise ValueError('检查选项无效。')
        with self.health_lock:
            if self.sharing_state['status']=='running' and not cancel:raise ValueError('正在复用文件，请等完成后再检查。')
            if cancel:
                if self.health_state['status']=='running':self.health_cancel.set();self.health_state['cancelRequested']=True
            elif self.health_state['status']!='running':
                self.health_cancel.clear();self.health_state={'status':'running','jobId':str(uuid.uuid4()),'progress':{'done':0,'total':0},'report':self.health_state['report'],'cancelRequested':False}
                threading.Thread(target=self._run_health,daemon=True).start()
        return self.health_status()

    def start_sharing(self,body):
        from maintenance import start_sharing
        return start_sharing(self,body)

    def _run_health(self):
        from storage import now
        try:
            resources,files,signature=self._health_catalog();issues=[];groups={};present=0;actual_bytes=0;unique_bytes=0;inodes=set();shared_files=0;identities={}
            known={a['id'] for a in files}
            with self.health_lock:self.health_state['progress']['total']=len(files)
            for index,a in enumerate(files):
                if self.health_cancel.is_set():
                    with self.health_lock:self.health_state['status']='cancelled'
                    return
                path=self.files/a['id'];issue=None
                try:
                    if path.is_symlink():raise OSError('symbolic link')
                    with path.open('rb') as stream:
                        before=path.stat();digest=hashlib.sha256()
                        for chunk in iter(lambda:stream.read(1024*1024),b''):
                            if self.health_cancel.is_set():break
                            digest.update(chunk)
                        after=path.stat()
                    if self.health_cancel.is_set():
                        with self.health_lock:self.health_state['status']='cancelled'
                        return
                    present+=1;actual_bytes+=after.st_size
                    identity=(after.st_dev,after.st_ino)
                    if identity in inodes:shared_files+=1
                    else:inodes.add(identity);unique_bytes+=after.st_size
                    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):issue='changed'
                    elif after.st_size!=a['size'] or digest.hexdigest()!=a['sha256']:issue='corrupt'
                    elif a['unlinked']:issue='unlinked'
                    elif not a['inTrash']:
                        groups.setdefault(a['sha256'],[]).append(a);identities[a['id']]=identity
                except FileNotFoundError:issue='missing'
                except OSError:issue='unreadable'
                if issue:issues.append({**a,'reason':issue})
                with self.health_lock:self.health_state['progress']['done']=index+1
            extras=[]
            for path in self.files.iterdir():
                if path.name not in known and path.is_file() and not path.name.endswith('.tmp'):extras.append(path.name)
            duplicates=[{'sha256':key,'size':items[0]['size'],'items':items,'storedCopies':len({identities[a['id']] for a in items})} for key,items in groups.items() if len(items)>1]
            report={'checkedAt':now(),'signature':signature,'stale':False,'resources':sum(not r['deleted'] for r in resources),'trashResources':sum(bool(r['deleted']) for r in resources),'attachments':len(files),'trashAttachments':sum(a['inTrash'] for a in files),'presentFiles':present,'storedBytes':actual_bytes,'duplicates':duplicates,'issues':issues,'unregisteredFiles':extras,'duplicateBytes':sum(g['size']*(len(g['items'])-1) for g in duplicates)}
            report.update(uniqueStoredBytes=unique_bytes,sharedBytes=actual_bytes-unique_bytes,sharedFiles=shared_files)
            with self.health_lock:self.health_state.update(status='complete',report=report,cancelRequested=False)
        except Exception:
            with self.health_lock:self.health_state.update(status='failed',error='检查未能完成。请确认数据目录可以读取，再重试。')
