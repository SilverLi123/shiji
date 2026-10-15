"""Disk-backed snapshots and validated staged restore. Attachment bytes stream."""
import hashlib
import io
import json
import os
import re
import sqlite3
import shutil
import threading
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
from pathlib import Path
from file_store import publish_file

CHUNK=1024*1024
MAX_ARCHIVE=16*1024*1024*1024
MAX_MANIFEST=64*1024*1024
MAX_FILE=64*1024*1024

def copy_checked(source,target,limit,expected=None):
    """Copy a bounded stream and retain only a short MIME prefix and hash state."""
    digest=hashlib.sha256();length=0;prefix=b''
    while True:
        block=source.read(CHUNK)
        if not block:break
        length+=len(block)
        if length>limit:raise ValueError('附件超过大小限制，备份可能损坏。')
        if len(prefix)<32:prefix=(prefix+block[:32])[:32]
        digest.update(block);target.write(block)
    if expected is not None and length!=expected:raise ValueError('附件长度不一致，备份可能损坏。')
    return length,digest.hexdigest(),prefix

def file_matches(path,attachment):
    if path.is_symlink() or not path.is_file():return False
    try:
        if path.stat().st_size!=attachment['size']:return False
        digest=hashlib.sha256()
        with path.open('rb') as source:
            for block in iter(lambda:source.read(CHUNK),b''):digest.update(block)
        return digest.hexdigest()==attachment['sha256']
    except OSError:return False

class BackupOperations:
    @contextmanager
    def backup_path(self,allow_missing=False):
        """Temporary valid ZIP persists only for the caller's download/atomic move."""
        with tempfile.TemporaryDirectory(dir=str(self.root),prefix='snapshot-') as directory:
            path=Path(directory)/'backup.zip'
            self._write_backup(path,allow_missing)
            yield path

    def _write_backup(self,path,allow_missing=False):
        from storage import dump,now,detect_mime,identifier
        directory=path.parent
        manifest=self._snapshot_inputs(directory,allow_missing)
        # Successful snapshots must remain within this format's restore caps.
        if any(len(manifest[key])>limit for key,limit in [('resources',10000),('attachments',20000),('collections',1000),('smartCollections',1000)]):
            raise ValueError('完整备份超过可恢复的数量限制（10000 条资源、20000 个附件、1000 个项目或智能集合），请分库整理后重试。')
        missing=[];damaged=[];valid=[]
        database=directory/'library.sqlite3'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as archive:
            archive.write(database,'library.sqlite3')
            for attachment in manifest['attachments']:
                aid=identifier(attachment['id']);file=directory/'pins'/aid
                if file.is_symlink() or not file.is_file():
                    missing.append(aid)
                    if not allow_missing:raise ValueError('有附件文件缺失或无法安全读取，完整备份失败；请用有效备份恢复或先运行库检查。')
                    continue
                try:
                    # Emergency snapshots keep readable original bytes even if damaged;
                    # their importable manifest excludes these broken references.
                    with file.open('rb') as source,archive.open('files/'+aid,'w',force_zip64=True) as target:
                        length,digest,prefix=copy_checked(source,target,MAX_ARCHIVE if allow_missing else MAX_FILE)
                    intact=length==attachment.get('size') and digest==attachment.get('sha256') and detect_mime(prefix)==attachment.get('mime')
                except OSError:
                    # A half-written entry is never delivered as a successful snapshot.
                    raise
                if not intact:
                    damaged.append(aid)
                    if not allow_missing:raise ValueError('有附件内容损坏，完整备份失败；请用有效备份恢复或先运行库检查。')
                else:valid.append(attachment)
            excluded=set(missing+damaged)
            if excluded:
                manifest['missingFiles']=missing
                if damaged:manifest['damagedFiles']=damaged
                manifest['attachments']=valid
                for resource in manifest['resources']:
                    if resource['coverId'] in excluded:resource['coverId']=''
                    resource['attachments']=[a for a in resource['attachments'] if a['id'] not in excluded]
            encoded=dump(manifest).encode()
            if len(encoded)>MAX_MANIFEST:raise ValueError('备份条目信息超过 64 MB，请分库整理后重试。')
            archive.writestr('manifest.json',encoded)
            if sum(e.file_size for e in archive.infolist())>MAX_ARCHIVE:raise ValueError('完整备份展开后超过 16 GB，请分库整理后重试。')
        if path.stat().st_size>MAX_ARCHIVE:raise ValueError('完整备份超过 16 GB，请分库整理后重试。')

    def backup_bytes(self,allow_missing=False):
        # Compatibility for callers explicitly requesting bytes; HTTP/auto-backup use paths.
        with self.backup_path(allow_missing) as path:return path.read_bytes()

    def _snapshot_inputs(self,directory,allow_missing=False):
        from storage import now,identifier
        database=directory/'library.sqlite3'
        # SQLite online backup runs without the application mutation lock.
        with self.connect() as source,sqlite3.connect(database) as target:source.backup(target,pages=128,sleep=.001)
        with sqlite3.connect(database) as c:
            c.row_factory=sqlite3.Row
            manifest={'format':'shiji-full-backup','version':2,'createdAt':now(),'resources':self._read_many(c,c.execute('SELECT * FROM resources').fetchall()),'collections':[r['name'] for r in c.execute('SELECT name FROM collections')],'collectionMeta':self._collection_meta(c),'smartCollections':[dict(r,filters=json.loads(r['filters'])) for r in c.execute('SELECT * FROM smart_collections')],'attachments':[dict(json.loads(r['payload']),deleted=bool(r['deleted'])) for r in c.execute('SELECT * FROM attachments')]}
        if any(len(manifest[key])>limit for key,limit in [('resources',10000),('attachments',20000),('collections',1000),('smartCollections',1000)]):raise ValueError('完整备份超过可恢复的数量限制，请分库整理后重试。')
        pins=directory/'pins';pins.mkdir()
        for attachment in manifest['attachments']:
            aid=identifier(attachment['id']);source=self.files/aid;target=pins/aid
            opened=None
            with self.lock:
                if source.is_symlink() or not source.is_file():
                    if allow_missing:continue
                    raise ValueError('有附件文件缺失或无法安全读取，备份失败。')
                try:os.link(source,target,follow_symlinks=False)
                except OSError:opened=source.open('rb')
            if opened is not None:
                # Opened inode stays readable through concurrent path replacement.
                with opened,target.open('wb') as output:copy_checked(opened,output,MAX_ARCHIVE if allow_missing else MAX_FILE)
        return manifest

    def _clear_snapshot_dirty(self,generation):
        with self.lock:
            if self._change_generation==generation:self.dirty=False

    def create_backup(self,allow_missing=False):
        from storage import now
        with self._backup_lock:
            generation=self._change_generation
            try:
                with self.backup_path(allow_missing) as path:
                    size=path.stat().st_size
                    name='shiji-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')+'.zip'
                    os.replace(path,self.backups/name)
            except (OSError,ValueError,sqlite3.Error) as e:self.backup_warning=str(e);raise
            self._clear_snapshot_dirty(generation)
            if not allow_missing:self.backup_warning=''
            self.prune_backups()
            return {'name':name,'size':size,'createdAt':now(),'kind':'zip'}

    def create_snapshot(self,at=None):
        from storage import dump,detect_mime
        at=at or datetime.now(timezone.utc)
        if at.tzinfo is None:raise ValueError('快照时间需要时区。')
        with self._backup_lock:
            generation=self._change_generation
            try:
                with tempfile.TemporaryDirectory(dir=str(self.root),prefix='snapshot-') as temporary:
                    staging=Path(temporary);manifest=self._snapshot_inputs(staging)
                    manifest['createdAt']=at.isoformat();objects=self.backups/'objects';objects.mkdir(exist_ok=True)
                    for a in manifest['attachments']:
                        target=objects/a['sha256']
                        if target.is_symlink():raise ValueError('备份附件存储路径无效。')
                        if file_matches(target,a):continue
                        partial=objects/(a['sha256']+'.tmp')
                        try:
                            with (staging/'pins'/a['id']).open('rb') as source,partial.open('wb') as output:length,digest,prefix=copy_checked(source,output,MAX_FILE)
                            if length!=a['size'] or digest!=a['sha256'] or detect_mime(prefix)!=a['mime']:raise ValueError('有附件内容损坏，快照失败。')
                            os.replace(partial,target);target.chmod(0o444)
                        finally:partial.unlink(missing_ok=True)
                    shutil.rmtree(staging/'pins')
                    (staging/'manifest.json').write_text(dump(manifest))
                    name='auto-'+at.strftime('%Y%m%d-%H%M%S-%f')+'-'+uuid.uuid4().hex[:8]
                    destination=self.backups/name;destination.mkdir()
                    for part in ('library.sqlite3','manifest.json'):os.replace(staging/part,destination/part)
                self._clear_snapshot_dirty(generation);self.backup_warning=''
                return {'name':name,'createdAt':at.isoformat(),'size':sum(p.stat().st_size for p in destination.iterdir()),'kind':'snapshot'}
            except (OSError,ValueError,sqlite3.Error) as e:self.backup_warning=str(e);raise

    def _history(self):
        rows=[]
        for path in self.backups.iterdir():
            if path.is_symlink():continue
            if path.name.startswith('auto-') and path.is_dir():
                try:
                    manifest=json.loads((path/'manifest.json').read_text());rows.append({'name':path.name,'size':sum(p.stat().st_size for p in path.iterdir() if p.is_file()),'createdAt':manifest['createdAt'],'kind':'snapshot'})
                except (OSError,ValueError,KeyError):continue
            elif re.fullmatch(r'shiji-[0-9-]+\.zip',path.name) and path.is_file():
                try:
                    stat=path.stat();rows.append({'name':path.name,'size':stat.st_size,'createdAt':datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat(),'kind':'zip'})
                except OSError:continue
        return sorted(rows,key=lambda r:r['createdAt'],reverse=True)

    def prune_backups(self,at=None):
        at=at or datetime.now(timezone.utc)
        with self._backup_lock:
            keep=set();buckets=set();rows=self._history()
            for row in rows:
                created=datetime.fromisoformat(row['createdAt']);age=at-created
                if age<timedelta(hours=24):bucket=('hour',created.strftime('%Y%m%d%H'))
                elif age<timedelta(days=7):bucket=('day',created.strftime('%Y%m%d'))
                elif age<timedelta(weeks=4):bucket=('week',created.strftime('%G%V'))
                else:continue
                key=(row['kind'],*bucket)
                if key not in buckets:keep.add(row['name']);buckets.add(key)
            # Always retain the newest successful backup of each format, even after a long idle period.
            for kind in ('zip','snapshot'):
                newest=next((r for r in rows if r['kind']==kind),None)
                if newest:keep.add(newest['name'])
            removed=0
            for row in rows:
                if row['name'] in keep:continue
                path=self.backups/row['name']
                if path.is_dir():shutil.rmtree(path)
                else:path.unlink()
                removed+=1
            references=set()
            for row in rows:
                if row['name'] in keep and row['kind']=='snapshot':references.update(a['sha256'] for a in json.loads((self.backups/row['name']/'manifest.json').read_text())['attachments'])
            objects=self.backups/'objects'
            if objects.is_dir():
                for path in objects.iterdir():
                    if re.fullmatch(r'[a-f0-9]{64}',path.name) and path.name not in references:path.unlink()
            return {'removed':removed}

    def backup_list(self):
        rows=self._history()
        return {'backups':[r for r in rows if r['kind']=='zip'],'snapshots':[r for r in rows if r['kind']=='snapshot'],'pending':self.dirty,'warning':self.backup_warning}

    def backup_file(self,name):
        if not re.fullmatch(r'shiji-[0-9-]+\.zip',name) or (self.backups/name).is_symlink() or not (self.backups/name).is_file():raise ValueError('备份不存在。')
        return self.backups/name

    def restore_zip(self,raw):
        """Accept old bytes callers and new file-backed HTTP uploads."""
        if isinstance(raw,(bytes,bytearray)):
            if len(raw)>MAX_ARCHIVE:raise ValueError('完整备份超过 16 GB。')
            source=io.BytesIO(raw)
        elif isinstance(raw,(str,Path)):
            source=Path(raw)
            if source.stat().st_size>MAX_ARCHIVE:raise ValueError('完整备份超过 16 GB。')
        else:raise ValueError('备份输入格式不正确。')
        with tempfile.TemporaryDirectory(dir=str(self.root),prefix='restore-') as directory:
            staging=Path(directory)
            try:
                with zipfile.ZipFile(source) as archive:
                    plan=self._validate_archive(archive,staging)
            except (zipfile.BadZipFile,KeyError,TypeError,AttributeError,json.JSONDecodeError,UnicodeDecodeError,NotImplementedError,RuntimeError) as e:
                raise ValueError('备份格式不正确或文件不完整。') from e
            return self._apply_archive(plan,staging)

    def _validate_archive(self,archive,staging):
        from storage import identifier,validate,text,normalize_url,palette,LICENSES,names,validate_filters,detect_mime
        from projects import import_tree
        entries=archive.infolist();entry_names=[e.filename for e in entries]
        if len(entries)>30000 or len(set(entry_names))!=len(entries) or sum(e.file_size for e in entries)>MAX_ARCHIVE:raise ValueError('备份展开后超过 16 GB，或包含重复文件。')
        for entry in entries:
            if entry.filename not in ('manifest.json','library.sqlite3') and not re.fullmatch(r'files/[a-f0-9-]{36}',entry.filename):raise ValueError('备份包含无效路径。')
            if entry.flag_bits&1 or entry.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):raise ValueError('请使用未加密的拾集 ZIP 备份。')
        manifest_info=archive.getinfo('manifest.json')
        if manifest_info.file_size>MAX_MANIFEST:raise ValueError('备份条目信息超过 64 MB。')
        with archive.open(manifest_info) as stream:manifest=json.loads(stream.read(MAX_MANIFEST+1))
        if not isinstance(manifest,dict) or manifest.get('format')!='shiji-full-backup' or manifest.get('version')!=2:raise ValueError('不是拾集完整备份。')
        source=manifest.get('resources',[]);attachments=manifest.get('attachments',[])
        if not isinstance(source,list) or not isinstance(attachments,list) or len(source)>10000 or len(attachments)>20000:raise ValueError('备份记录格式不正确。')
        items=[];known=set();urls=set()
        for raw in source:
            rid=identifier(raw.get('id',''),'资源 ID')
            if rid in known or (raw.get('url') and normalize_url(raw['url']) in urls):raise ValueError('备份包含重复资源。')
            item=validate({**raw,'coverId':'','parentId':''});item['id']=rid;item['deleted']=raw.get('deleted',False);item['coverId']=text(raw.get('coverId',''),80,'封面');item['parentId']=text(raw.get('parentId',''),80,'来源')
            if not isinstance(item['deleted'],bool):raise ValueError('回收站记录格式不正确。')
            items.append(item);known.add(rid)
            if item['url']:urls.add(item['url'])
        aids=set();clean_attachments=[]
        for attachment in attachments:
            aid=attachment.get('id')
            if not isinstance(aid,str) or not re.fullmatch(r'[a-f0-9-]{36}',aid) or aid in aids or attachment.get('resourceId') not in known:raise ValueError('附件引用无效。')
            size=attachment.get('size');digest=attachment.get('sha256')
            if type(size) is not int or not 0<size<=MAX_FILE or not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('附件信息格式不正确。')
            info=archive.getinfo('files/'+aid)
            if info.file_size!=size:raise ValueError('附件校验失败，备份可能损坏。')
            with archive.open(info) as incoming,(staging/aid).open('wb') as target:
                length,actual,prefix=copy_checked(incoming,target,MAX_FILE,size)
            if actual!=digest:raise ValueError('附件校验失败，备份可能损坏。')
            if attachment.get('mime')!=detect_mime(prefix):raise ValueError('附件类型校验失败。')
            clean=dict(attachment);clean['name']=re.sub(r'[\x00-\x1f/\\]','_',text(attachment.get('name'),240,'附件名称',True));clean['colors']=palette(attachment.get('colors',[]))
            for key in ('sourceUrl','author','licenseUrl'):clean[key]=text(attachment.get(key,''),200 if key=='author' else 4000,key)
            for key in ('sourceUrl','licenseUrl'):
                if clean[key]:clean[key]=normalize_url(clean[key])
            if clean.get('license') not in LICENSES or not isinstance(clean.get('deleted',False),bool):raise ValueError('附件信息格式不正确。')
            clean_attachments.append(clean);aids.add(aid)
        byaid={a['id']:a for a in clean_attachments}
        for item in items:
            if item['parentId'] and (item['parentId'] not in known or item['parentId']==item['id']):raise ValueError('资源来源引用无效。')
            cover=byaid.get(item['coverId'])
            if item['coverId'] and (not cover or cover['resourceId']!=item['id'] or not cover['mime'].startswith('image/') or cover.get('deleted')):raise ValueError('封面引用无效。')
        collections=names(manifest.get('collections',[]),1000);meta=import_tree(manifest.get('collectionMeta',[]),collections)
        smart_raw=manifest.get('smartCollections',[])
        if not isinstance(smart_raw,list) or len(smart_raw)>1000:raise ValueError('智能集合记录格式不正确。')
        smart=[{'id':identifier(s.get('id',''),'集合 ID'),'name':text(s.get('name',''),80,'集合名称',True),'filters':validate_filters(s.get('filters'))} for s in smart_raw]
        return items,clean_attachments,collections,meta,smart

    def _apply_archive(self,plan,staging):
        from storage import dump
        items,attachments,collections,meta,smart=plan
        with self.lock:snapshot_dirty=self.dirty
        before=self.create_backup(allow_missing=True)
        with self.lock:
            previous_dirty=self.dirty or snapshot_dirty
            written=[];originals=[];idmap={};restored=skipped=repaired=0
            rollback=staging/'originals';rollback.mkdir()
            try:
                with self.connect() as c:
                    self._merge_collection_meta(c,meta)
                    for item in items:
                        row=c.execute('SELECT * FROM resources WHERE '+('url=?' if item['url'] else 'id=?'),(item['url'] or item['id'],)).fetchone()
                        if row:
                            idmap[item['id']]=row['id']
                            if not row['deleted']:skipped+=1;continue
                            restored+=1
                        else:
                            collision=c.execute('SELECT id FROM resources WHERE id=?',(item['id'],)).fetchone()
                            idmap[item['id']]=str(uuid.uuid4()) if collision else item['id'];restored+=1
                    amap={}
                    for attachment in attachments:
                        aid=attachment['id'];existing=c.execute('SELECT * FROM attachments WHERE id=?',(aid,)).fetchone();destid=idmap[attachment['resourceId']]
                        reuse=existing and json.loads(existing['payload'])['sha256']==attachment['sha256'] and existing['resource_id']==destid
                        if reuse:
                            amap[aid]=aid;destination=self.files/aid
                            if file_matches(destination,attachment):continue
                            if destination.is_dir():raise ValueError('附件位置被文件夹占用，请先检查数据目录。')
                            if destination.exists() or destination.is_symlink():
                                old=rollback/aid;os.replace(destination,old);originals.append((old,destination))
                            publish_file(self,c,attachment,staged=staging/aid);written.append(destination);repaired+=1
                            continue
                        new_id=str(uuid.uuid4()) if existing else aid;amap[aid]=new_id;clean={**attachment,'id':new_id,'resourceId':destid};deleted=int(clean.pop('deleted',False));destination=self.files/new_id
                        if destination.exists() or destination.is_symlink():raise ValueError('附件存储冲突，未覆盖已有文件。')
                        publish_file(self,c,clean,staged=staging/aid);written.append(destination)
                        c.execute('INSERT INTO attachments VALUES(?,?,?,?)',(new_id,destid,dump(clean),deleted))
                    for item in items:
                        target=idmap[item['id']];row=c.execute('SELECT * FROM resources WHERE id=?',(target,)).fetchone()
                        if row and not row['deleted']:continue
                        value={**item,'id':target,'coverId':amap.get(item['coverId'],''),'parentId':idmap.get(item['parentId'],'')};deleted=int(value.pop('deleted'));key=value['url'] or 'shiji:'+target
                        c.execute('INSERT INTO resources VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET url=excluded.url,payload=excluded.payload,deleted=excluded.deleted',(target,key,dump(value),deleted));self._projects(c,value)
                    for name in collections:c.execute('INSERT OR IGNORE INTO collections(name) VALUES(?)',(name,))
                    for collection in smart:c.execute('INSERT OR IGNORE INTO smart_collections VALUES(?,?,?)',(collection['id'],collection['name'],dump(collection['filters'])))
                self.invalidate_trash_undo(list(idmap.values()))
                self.dirty=True
            except Exception:
                for path in reversed(written):path.unlink(missing_ok=True)
                for old,destination in reversed(originals):os.replace(old,destination)
                self.dirty=previous_dirty
                raise
            return {'restored':restored,'skipped':skipped,'repairedFiles':repaired,'beforeBackup':before['name']}
