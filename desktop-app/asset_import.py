"""Read-only asset planning and atomic, retry-safe individual imports."""
import hashlib
import json
import re
import uuid
from file_store import publish_file

MAX_FILES=200
MAX_FILE=64*1024*1024
MAX_TOTAL=2*1024*1024*1024

def relative_path(value):
    from storage import text
    value=text(value,1000,'原文件夹路径')
    if value and (value.startswith(('/', '\\')) or '\\' in value or ':' in value or any(p in ('','.', '..') for p in value.split('/')) or re.search(r'[\x00-\x1f\x7f]',value)):
        raise ValueError('请使用所选文件夹内的相对路径。')
    return value

def options(raw):
    from storage import validate
    if not isinstance(raw,dict):raise ValueError('导入信息格式不正确。')
    fields=('tags','projects','sourceUrl','author','licenseUrl','license','price')
    candidate=validate({'kind':'file','title':'素材',**{k:raw[k] for k in fields if k in raw}})
    return {k:candidate[k] for k in fields}

def category(mime,name):
    if mime.startswith('image/'):return '美术素材'
    if mime.startswith('audio/'):return '音频'
    if mime.startswith('video/'):return '视频'
    if re.search(r'\.(woff2?|ttf|otf)$',name,re.I):return '字体'
    return '其他'

class AssetImportOperations:
    def validate_asset_options(self,body):
        value=options(body)
        with self.lock,self.connect() as c:
            known={r['name'] for r in c.execute('SELECT name FROM collections')}
            if any(n not in known for n in value['projects']):raise ValueError('所选项目已不存在，请重新选择项目。')
        return {'options':value}

    def _asset_duplicates(self,c,wanted):
        """Hash only candidate files. A missing, corrupt or linked copy is not a match."""
        from storage import identifier
        matches={}
        rows=c.execute('SELECT a.payload,r.id,r.deleted,r.payload AS resource FROM attachments a JOIN resources r ON a.resource_id=r.id WHERE a.deleted=0 ORDER BY r.deleted,a.rowid')
        for row in rows:
            item=json.loads(row['payload']);key=(item.get('sha256'),item.get('size'))
            if key not in wanted:continue
            try:
                aid=identifier(item['id']);path=self.files/aid
                if path.is_symlink() or not path.is_file() or path.stat().st_size!=key[1]:continue
                digest=hashlib.sha256()
                with path.open('rb') as f:
                    for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
                if digest.hexdigest()!=key[0]:continue
            except (OSError,ValueError):continue
            resource=json.loads(row['resource'])
            matches.setdefault(key,{'id':row['id'],'title':resource['title'],'deleted':bool(row['deleted'])})
        return matches

    def preview_assets(self,body):
        from storage import text
        files=body.get('files')
        if not isinstance(files,list) or not files or len(files)>MAX_FILES:raise ValueError('一次请选择 1 至 200 个文件。')
        total=0;items=[];seen=set();wanted=set()
        for number,raw in enumerate(files):
            if not isinstance(raw,dict):raise ValueError('文件清单格式不正确。')
            try:
                name=text(raw.get('name',''),240,'文件名称',True)
                path=relative_path(raw.get('path',''))
                length=raw.get('size')
                if type(length) is not int or length<1 or length>MAX_FILE:raise ValueError('文件为空或超过 64 MB，请移除后重新选择。')
                digest=text(raw.get('sha256',''),64,'文件校验值',True)
                if not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('无法校验文件，请重新选择。')
                total+=length;wanted.add((digest,length))
                item={'index':number,'name':name,'path':path,'size':length,'sha256':digest,'title':name[:200],'status':'new','message':'可以导入','existingId':''}
            except ValueError as e:
                item={'index':number,'name':str(raw.get('name',''))[:240],'path':'','size':0,'status':'invalid','message':str(e),'existingId':''}
            items.append(item)
        if total>MAX_TOTAL:raise ValueError('本批文件超过 2 GB，请分批选择。')
        with self.lock,self.connect() as c:matches=self._asset_duplicates(c,wanted)
        for item in items:
            if item['status']=='invalid':continue
            key=(item['sha256'],item['size'])
            match=matches.get(key)
            if match:item.update(status='trash' if match['deleted'] else 'existing',message='相同内容在回收站；可恢复已有资源，或勾选另存副本' if match['deleted'] else '已有相同内容；保留原收藏，勾选则另存副本',existingId=match['id'],existingTitle=match['title'])
            elif key in seen:item.update(status='duplicate',message='与本批前面的文件相同；勾选则另存副本')
            seen.add(key)
        return {'items':items,'totalBytes':total,'new':sum(i['status']=='new' for i in items)}

    def import_asset(self,raw,metadata):
        from storage import text,identifier,validate,detect_mime,palette,dump,now
        if not raw or len(raw)>MAX_FILE:raise ValueError('单个文件须为 1 字节至 64 MB。')
        if not isinstance(metadata,dict):raise ValueError('导入信息格式不正确。')
        request=identifier(metadata.get('requestId',''),'导入请求 ID')
        name=text(metadata.get('name',''),240,'文件名称',True)
        name=re.sub(r'[\x00-\x1f/\\]','_',name)
        title=text(metadata.get('title',name[:200]),200,'资源名称',True)
        path=relative_path(metadata.get('path',''))
        policy=metadata.get('duplicatePolicy','skip')
        if policy not in ('skip','copy'):raise ValueError('重复文件选项无效。')
        settings=options(metadata)
        colors=palette(metadata.get('colors',[]));mime=detect_mime(raw)
        digest=hashlib.sha256(raw).hexdigest()
        expected=metadata.get('sha256',digest)
        if expected!=digest:raise ValueError('文件与预览的内容不一致，请重新选择。')
        fingerprint=hashlib.sha256(dump([digest,name,title,path,policy,settings,colors]).encode()).hexdigest()
        aid=str(uuid.uuid4());destination=self.files/aid;written=False
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    receipt=c.execute('SELECT * FROM asset_receipts WHERE request_id=?',(request,)).fetchone()
                    if receipt:
                        if receipt['fingerprint']!=fingerprint:raise ValueError('此导入请求内容已改变，请重新选择文件。')
                        resource=self._get(c,receipt['resource_id'])
                        return {'status':'saved','resource':resource,'replayed':True}
                    known={r['name'] for r in c.execute('SELECT name FROM collections')}
                    if any(n not in known for n in settings['projects']):raise ValueError('所选项目已不存在，请重新选择项目。')
                    if policy=='skip':
                        match=self._asset_duplicates(c,{(digest,len(raw))}).get((digest,len(raw)))
                        if match:return {'status':'skipped','existingId':match['id'],'deleted':match['deleted'],'message':'已找到相同内容，保留已有资源。'}
                    resource=validate({'kind':'file','title':title,'category':category(mime,name),'inbox':True,'colors':colors if mime.startswith('image/') else [],'notes':('原文件夹路径：'+path) if path else '',**settings})
                    attachment={'id':aid,'resourceId':resource['id'],'name':name,'mime':mime,'size':len(raw),'sha256':digest,'createdAt':now(),'colors':colors if mime.startswith('image/') else [],**{k:settings[k] for k in ('sourceUrl','author','licenseUrl','license')}}
                    publish_file(self,c,attachment,raw=raw);written=True
                    resource=self._write(c,resource)
                    attachment['resourceId']=resource['id']
                    c.execute('INSERT INTO attachments VALUES(?,?,?,0)',(aid,resource['id'],dump(attachment)))
                    if mime.startswith('image/'):
                        resource=self._get(c,resource['id']);resource['coverId']=aid
                        self._write(c,resource,resource)
                    c.execute('INSERT INTO asset_receipts VALUES(?,?,?)',(request,fingerprint,resource['id']))
                    result={'status':'saved','resource':self._get(c,resource['id']),'replayed':False}
                self.dirty=True
                return result
            except Exception:
                if written:destination.unlink(missing_ok=True)
                self.dirty=previous_dirty
                raise
