"""Guarded resource sync; desktop schema3 and backup manifest2 are unchanged."""
import hashlib,json,re,threading,time,uuid
from pathlib import Path
from storage import validate,dump,detect_mime,identifier

MAX_FILE=64*1024*1024
MAX_TOTAL=512*1024*1024
def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def attachment_id(value):
 if not isinstance(value,str) or not re.fullmatch(r'[a-f0-9-]{36}',value):raise ValueError('附件 ID 无效。')
 return value
class RevisionConflict(ValueError):pass

class SyncEngine:
 def __init__(self,store):
  self.store=store;self.lock=threading.RLock();self.staging=store.root/'mobile-sync'/'staging';self.staging.mkdir(parents=True,exist_ok=True,mode=0o700)
  with store.lock,store.connect() as c:
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('mobileSyncLibraryId',str(uuid.uuid4())))
   self.library_id=c.execute('SELECT value FROM settings WHERE key=?',('mobileSyncLibraryId',)).fetchone()[0]
 def _snapshot(self,c):
  resources=[self.store._read(c,row) for row in c.execute('SELECT * FROM resources ORDER BY id').fetchall()]
  content={'version':1,'libraryId':self.library_id,'resources':resources,'collections':[r['name'] for r in c.execute('SELECT name FROM collections ORDER BY name')],'collectionMeta':self.store._collection_meta(c),'smartCollections':[dict(r,id=r['id'],filters=json.loads(r['filters'])) for r in c.execute('SELECT * FROM smart_collections ORDER BY id')]}
  return {**content,'revision':digest(content)}
 def snapshot(self):
  with self.store.lock,self.store.connect() as c:return self._snapshot(c)
 def stage(self,aid,raw,sha):
  aid=attachment_id(aid)
  if not raw or len(raw)>MAX_FILE or not isinstance(sha,str) or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('附件大小或 SHA-256 校验失败。')
  with self.lock,self.store.lock:
   existing=self.store.files/aid
   if existing.exists():
    if existing.is_symlink() or existing.read_bytes()!=raw:raise ValueError('同 ID 附件内容不同，未覆盖原文件。')
    return
   for old in self.staging.iterdir():
    if old.is_file() and old.stat().st_mtime<time.time()-24*3600:old.unlink()
   total=sum(p.stat().st_size for p in self.staging.iterdir() if p.is_file())
   destination=self.staging/aid
   if total-(destination.stat().st_size if destination.exists() else 0)+len(raw)>MAX_TOTAL:raise ValueError('待同步附件超过 512 MB，请稍后重试。')
   temporary=self.staging/(aid+'.tmp');temporary.write_bytes(raw);temporary.chmod(0o600);temporary.replace(destination)
 def file(self,aid):
  aid=attachment_id(aid)
  with self.store.lock:
   with self.store.connect() as c:
    row=c.execute('SELECT payload FROM attachments WHERE id=? AND deleted=0',(aid,)).fetchone()
    if not row:raise ValueError('附件不存在。')
    metadata=json.loads(row[0]);path=self.store.files/aid
    if path.is_symlink() or not path.is_file():raise ValueError('附件缺失。')
    raw=path.read_bytes()
    if len(raw)!=metadata['size'] or hashlib.sha256(raw).hexdigest()!=metadata['sha256']:raise ValueError('电脑附件校验失败，请恢复有效备份。')
    return raw,metadata
 def commit(self,body):
  if not isinstance(body,dict) or set(body)!={'version','libraryId','expectedRevision','requestId','resources'} or body['version']!=1 or body['libraryId']!=self.library_id:raise ValueError('同步库或协议不匹配，请重新配对。')
  request=identifier(body['requestId']);incoming=body['resources']
  if not isinstance(incoming,list) or len(incoming)>10000:raise ValueError('同步资源数量无效。')
  fingerprint=digest(body);published=[]
  with self.lock,self.store.lock:
   previous_dirty=self.store.dirty
   try:
    with self.store.connect() as c:
     # Read and revision check share the same database transaction as the writes.
     c.execute('BEGIN IMMEDIATE')
     receipt_key='mobileSyncReceipt:'+request
     receipt=c.execute('SELECT value FROM settings WHERE key=?',(receipt_key,)).fetchone()
     if receipt:
      if receipt[0]!=fingerprint:raise ValueError('重试请求内容已改变。')
      return self._snapshot(c)
     current=self._snapshot(c)
     if body['expectedRevision']!=current['revision']:raise RevisionConflict('电脑资料已变化，未覆盖任何修改。请重新同步。')
     known={r['id']:r for r in current['resources']};clean=[];ids=set();aids=set();payloads={};total=0
     for raw in incoming:
      if not isinstance(raw,dict):raise ValueError('同步资源格式无效。')
      rid=identifier(raw.get('id'))
      if rid in ids:raise ValueError('资源 ID 重复。')
      ids.add(rid);existing=known.get(rid)
      seed=existing or {'id':rid,'createdAt':raw.get('createdAt'),'projectNotes':{}}
      item=validate(raw,seed)
      if not isinstance(raw.get('deleted',False),bool):raise ValueError('回收站标记无效。')
      item['deleted']=raw.get('deleted',False)
      attachments=raw.get('attachments',[])
      if not isinstance(attachments,list) or len(attachments)>20000:raise ValueError('附件列表无效。')
      item['attachments']=[]
      for a in attachments:
       if not isinstance(a,dict):raise ValueError('附件格式无效。')
       aid=attachment_id(a.get('id'))
       if aid in aids or a.get('resourceId')!=rid:raise ValueError('附件归属或 ID 无效。')
       aids.add(aid)
       if not isinstance(a.get('name'),str) or not a['name'] or len(a['name'])>240 or any(x in a['name'] for x in ('/','\\','\0')):raise ValueError('附件名称无效。')
       if type(a.get('size')) is not int or not 0<a['size']<=MAX_FILE:raise ValueError('附件超过上限。')
       path=self.store.files/aid
       existing_attachment=c.execute('SELECT resource_id,payload FROM attachments WHERE id=?',(aid,)).fetchone()
       if existing_attachment and existing_attachment[0]!=rid:raise ValueError('附件 ID 已属于另一资源。')
       if not path.exists():path=self.staging/aid
       if path.is_symlink() or not path.is_file():raise ValueError('附件未传输完成，请重试。')
       new_file=path.parent==self.staging
       hash_=hashlib.sha256();size=0;header=b''
       with path.open('rb') as f:
        while True:
         chunk=f.read(1024*1024)
         if not chunk:break
         if not header:header=chunk[:64]
         size+=len(chunk);hash_.update(chunk)
       if new_file:total+=size
       if total>MAX_TOTAL or size!=a['size'] or hash_.hexdigest()!=a.get('sha256') or detect_mime(header)!=a.get('mime'):raise ValueError('附件大小、类型或 SHA-256 无效。')
       if existing_attachment:
        old=json.loads(existing_attachment[1])
        if old.get('sha256')!=a['sha256'] or old.get('size')!=a['size']:raise ValueError('不能覆盖同 ID 附件内容。')
       # Reuse desktop validation for attachment authorization/source metadata.
       probe=validate({'title':'附件','kind':'file','author':a.get('author',''),'sourceUrl':a.get('sourceUrl',''),'licenseUrl':a.get('licenseUrl',''),'license':a.get('license','待确认'),'colors':a.get('colors',[])})
       normalized={**a,**{k:probe[k] for k in ('author','sourceUrl','licenseUrl','license','colors')},'deleted':False}
       item['attachments'].append(normalized);payloads[aid]=(path,normalized)
      clean.append(item)
     resulting={**known,**{r['id']:r for r in clean}};urls=set()
     for r in resulting.values():
      if r['url']:
       if r['url'] in urls:raise ValueError('同一网址有不同资源 ID，请先处理同步冲突。')
       urls.add(r['url'])
      if r.get('parentId') and r['parentId'] not in resulting:raise ValueError('来源资源缺失。')
      if r.get('coverId') and not any(a['id']==r['coverId'] and a['mime'].startswith('image/') for a in r['attachments']):raise ValueError('封面引用无效。')
     for aid,(source,a) in payloads.items():
      destination=self.store.files/aid
      if not destination.exists():
       # Exclusive create protects immutable files even against an external writer.
       with destination.open('xb') as f,source.open('rb') as src:
        published.append(destination)
        while True:
         chunk=src.read(1024*1024)
         if not chunk:break
         f.write(chunk)
     for r in clean:
      attachments=r.pop('attachments');deleted=r.pop('deleted')
      c.execute('INSERT INTO resources(id,url,payload,deleted) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET url=excluded.url,payload=excluded.payload,deleted=excluded.deleted',(r['id'],r['url'] or 'shiji:'+r['id'],dump(r),int(deleted)))
      self.store._projects(c,r)
      c.execute('UPDATE attachments SET deleted=1 WHERE resource_id=?',(r['id'],))
      for a in attachments:c.execute('INSERT INTO attachments VALUES(?,?,?,0) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,deleted=0',(a['id'],r['id'],dump(a)))
      previous=known.get(r['id'])
      if deleted:self.store.invalidate_capture(c,[r['id']])
      elif previous is None or previous['url']!=r['url']:
       # Schedule after installing phone attachments so manual covers win. The
       # derived task and sync receipt commit atomically with the original URL.
       self.store.enqueue_capture(c,r)
     c.execute('INSERT INTO settings VALUES(?,?)',(receipt_key,fingerprint))
     # Bounded retry receipts; keep the latest 500 operations.
     c.execute("DELETE FROM settings WHERE key IN (SELECT key FROM settings WHERE key LIKE 'mobileSyncReceipt:%' ORDER BY rowid DESC LIMIT -1 OFFSET 500)")
     result=self._snapshot(c)
    if clean:self.store.dirty=True
    for aid in payloads:
     try:(self.staging/aid).unlink(missing_ok=True)
     except OSError:pass # Committed payloads remain valid; cleanup must not undo a commit.
    return result
   except Exception:
    for path in published:path.unlink(missing_ok=True)
    self.store.dirty=previous_dirty
    raise
