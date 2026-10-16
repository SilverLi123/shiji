"""Local persistence, migrations and resource operations."""
import hashlib
import io
import json
import re
import secrets
import sqlite3
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from projects import ProjectOperations, import_tree
from search_index import SearchOperations
from resource_query import QueryOperations,color_distance
from link_import import LinkImportOperations
from health import HealthOperations
from bookmarks import BookmarkOperations
from asset_import import AssetImportOperations
from backups import BackupOperations
from recovery import RecoveryOperations
from preview_jobs import PreviewOperations
from file_store import publish_file
from edits import GuardedEditOperations, EditConflict
from quick_capture import QuickCaptureOperations
from capture_jobs import CaptureOperations
from capture_receipts import CaptureReceiptOperations, fingerprint as clip_fingerprint, request_identifier

CATEGORIES=['开发工具','美术素材','UI / 设计','音频','视频','字体','3D','灵感','其他']
PRICES=['待确认','免费','部分免费','付费']
LICENSES=['待确认','允许商用','需署名','仅个人使用']
KINDS=['website','file','code','prompt']
def now():return datetime.now(timezone.utc).isoformat()
def dump(value):return json.dumps(value,ensure_ascii=False)
def text(value,limit,label,required=False):
    if not isinstance(value,str) or len(value)>limit or (required and not value.strip()):raise ValueError(label+'格式不正确或太长。')
    return value.strip()
def identifier(value,label='ID'):
    value=text(value,80,label,True)
    if not re.fullmatch(r'[A-Za-z0-9_-]+',value):raise ValueError(label+'格式不正确。')
    return value
def names(values,limit=30,length=80):
    if not isinstance(values,list) or len(values)>limit:raise ValueError('列表格式不正确或数量太多。')
    return list(dict.fromkeys(text(x,length,'名称',True) for x in values))
def normalize_url(value):
    value=text(value,4000,'网址',True)
    if any(c.isspace() for c in value):raise ValueError('网址中不能包含空格或换行。')
    if '://' not in value:value='https://'+value
    try:
        p=urlsplit(value)
        if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:raise ValueError()
        host=p.hostname.lower();port=p.port
        if ':' in host:host='['+host+']'
        netloc=host+(':'+str(port) if port and port!=(443 if p.scheme=='https' else 80) else '')
        return urlunsplit((p.scheme,netloc,p.path or '/',p.query,''))
    except ValueError:raise ValueError('网址须使用 http 或 https，且不能包含账户密码。')
def palette(values):
    if not isinstance(values,list) or len(values)>8 or any(not isinstance(x,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',x) for x in values):raise ValueError('颜色须为六位十六进制色值。')
    return list(dict.fromkeys(x.lower() for x in values))
def validate(raw,existing=None):
    if not isinstance(raw,dict):raise ValueError('资源格式不正确。')
    if raw.get('_summary') is True:raise ValueError('资源摘要不能直接保存，请先读取完整详情。')
    item={**(existing or {}),**raw};item['id']=existing['id'] if existing else str(uuid.uuid4())
    item['title']=text(item.get('title',''),200,'名称',True)
    item['kind']=item.get('kind','website')
    if item['kind'] not in KINDS:raise ValueError('请选择有效资源形式。')
    u=text(item.get('url',''),4000,'网址');item['url']=normalize_url(u) if u else ''
    if item['kind']=='website' and not item['url']:raise ValueError('网站资源需要填写网址。')
    for key,limit in [('notes',10000),('description',1000),('snippet',100000),('language',40),('author',200),('sourceUrl',4000),('licenseUrl',4000),('thumbnail',4000),('favicon',4000),('coverId',80),('parentId',80)]:item[key]=text(item.get(key,''),limit,key)
    for key in ('sourceUrl','licenseUrl','favicon','thumbnail'):
        if item[key]:item[key]=normalize_url(item[key])
    for key,values in [('category',CATEGORIES),('price',PRICES),('license',LICENSES)]:
        item[key]=item.get(key,values[-1] if key=='category' else values[0])
        if item[key] not in values:raise ValueError('请选择有效的'+key+'。')
    item['tags']=names(item.get('tags',[]),30,50)
    if 'projects' in raw:item['projects']=names(raw['projects'])
    elif 'collection' in raw:item['projects']=[text(raw['collection'],80,'项目')] if raw['collection'] else []
    else:item['projects']=names(item.get('projects',[]))
    item['collection']=item['projects'][0] if item['projects'] else ''
    pn=item.get('projectNotes',{})
    if not isinstance(pn,dict):raise ValueError('项目备注格式不正确。')
    pn={**(existing or {}).get('projectNotes',{}),**pn}
    if len(pn)>1000:raise ValueError('保留的项目备注数量太多。')
    retained={}
    for p,note in pn.items():
        if text(p,80,'备注项目名称',True)!=p:raise ValueError('备注项目名称格式不正确。')
        retained[p]=text(note,2000,'项目备注')
    for p in item['projects']:retained.setdefault(p,'')
    if len(retained)>1000:raise ValueError('保留的项目备注数量太多。')
    item['projectNotes']=retained
    item['colors']=palette(item.get('colors',[]))
    for field in ('favorite','inbox','demo'):
        value=item.get(field,False)
        if not isinstance(value,bool):raise ValueError(field+'应为布尔值。')
        item[field]=value
    created=existing['createdAt'] if existing else item.get('createdAt',now())
    try:datetime.fromisoformat(text(created,40,'收藏时间').replace('Z','+00:00'))
    except ValueError:raise ValueError('收藏时间格式不正确。')
    item['createdAt']=created;item['updatedAt']=now()
    # Internal status is not editable through public resource writes.
    item['linkStatus']=(existing or {}).get('linkStatus','unchecked');item['linkCheckedAt']=(existing or {}).get('linkCheckedAt','')
    return {k:v for k,v in item.items() if k not in ('attachments','deleted','deletedAt')}
class StoreConnection(sqlite3.Connection):
    """A transaction context owns its connection, including query/page-cache resources."""
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

class NoteConflict(ValueError):
    def __init__(self,current,resource=None):
        self.current=current;self.resource=resource;super().__init__('备注已在其他页面修改，请比较最新内容后再保存。')

class Duplicate(ValueError):
    def __init__(self,rid):self.rid=rid;super().__init__('这个网址已经收藏过了，请编辑已有资源。')

def validate_filters(raw):
    if not isinstance(raw,dict):raise ValueError('筛选格式不正确。')
    result={}
    for key in ('search','category','price','license','kind','linkStatus','color','collection'):
        result[key]=text(raw.get(key,''),200 if key=='search' else 80,'筛选条件')
    result['tags']=names(raw.get('tags',[]),30,50)
    for key in ('favorite','inbox','hasAssets','isSnippet'):
        if key in raw:
            if not isinstance(raw[key],bool):raise ValueError('筛选条件无效。')
            result[key]=raw[key]
    choices={'category':['']+CATEGORIES,'price':['']+PRICES,'license':['']+LICENSES,'kind':['']+KINDS,'linkStatus':['','unchecked','ok','broken','unknown']}
    if any(result[k] not in v for k,v in choices.items()):raise ValueError('筛选条件无效。')
    if result['color']:palette([result['color']])
    from filters import advanced_filters
    return advanced_filters(raw,result)

class Store(QueryOperations,SearchOperations,CaptureReceiptOperations,CaptureOperations,QuickCaptureOperations,PreviewOperations,RecoveryOperations,GuardedEditOperations,ProjectOperations,LinkImportOperations,HealthOperations,BookmarkOperations,AssetImportOperations,BackupOperations):
    def __init__(self,directory):
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True)
        self.db=self.root/'library.sqlite3';self.files=self.root/'files';self.files.mkdir(exist_ok=True)
        self.backups=self.root/'backups';self.backups.mkdir(exist_ok=True)
        self.lock=threading.RLock();self._backup_lock=threading.RLock();self._change_generation=0;self.dirty=False;self.backup_warning=''
        self.init_health()
        if self.db.exists():
            with sqlite3.connect(self.db) as c:
                version=c.execute('PRAGMA user_version').fetchone()[0]
                if version<3:
                    with sqlite3.connect(self.root/('before-upgrade.sqlite3' if version<2 else 'before-folders.sqlite3')) as d:c.backup(d)
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,url TEXT NOT NULL UNIQUE,payload TEXT NOT NULL,deleted INTEGER NOT NULL DEFAULT 0)')
            c.execute("CREATE TABLE IF NOT EXISTS collections(name TEXT PRIMARY KEY,parent TEXT NOT NULL DEFAULT '',auto_tags TEXT NOT NULL DEFAULT '[]',archived INTEGER NOT NULL DEFAULT 0)")
            columns={r['name'] for r in c.execute('PRAGMA table_info(collections)')}
            for name,definition in [('parent',"TEXT NOT NULL DEFAULT ''"),('auto_tags',"TEXT NOT NULL DEFAULT '[]'"),('archived','INTEGER NOT NULL DEFAULT 0')]:
                if name not in columns:c.execute('ALTER TABLE collections ADD COLUMN '+name+' '+definition)
            c.execute('CREATE TABLE IF NOT EXISTS resource_projects(resource_id TEXT NOT NULL,name TEXT NOT NULL,note TEXT NOT NULL DEFAULT "",PRIMARY KEY(resource_id,name))')
            c.execute('CREATE TABLE IF NOT EXISTS attachments(id TEXT PRIMARY KEY,resource_id TEXT NOT NULL,payload TEXT NOT NULL,deleted INTEGER NOT NULL DEFAULT 0)')
            c.execute('CREATE TABLE IF NOT EXISTS asset_receipts(request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, resource_id TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS smart_collections(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,filters TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            self.init_capture_jobs(c)
            self.init_capture_receipts(c)
            if c.execute('PRAGMA user_version').fetchone()[0]<2:
                for row in c.execute('SELECT * FROM resources').fetchall():
                    old=json.loads(row['payload']);old.setdefault('createdAt',now());old.setdefault('url',row['url'])
                    item=validate(old,{**old,'id':row['id']});item['updatedAt']=old.get('updatedAt',now())
                    c.execute('UPDATE resources SET payload=? WHERE id=?',(dump(item),row['id']));self._projects(c,item)
            c.execute('PRAGMA user_version=3')
            c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('clipToken',secrets.token_urlsafe(32)))
        self.init_search()
        self.init_previews()
        self.cleanup_restore_staging()
    def connect(self):
        c=sqlite3.connect(str(self.db),timeout=15,factory=StoreConnection);c.row_factory=sqlite3.Row;c.execute('PRAGMA mmap_size=67108864');c.create_function('color_distance',2,color_distance,deterministic=True);return c
    def _projects(self,c,item):
        c.execute('DELETE FROM resource_projects WHERE resource_id=?',(item['id'],))
        for name in item['projects']:
            c.execute('INSERT OR IGNORE INTO collections(name) VALUES(?)',(name,))
            c.execute('INSERT INTO resource_projects VALUES(?,?,?)',(item['id'],name,item['projectNotes'].get(name,'')))
    def _read(self,c,row):
        item=json.loads(row['payload']);item['deleted']=bool(row['deleted'])
        item['attachments']=[json.loads(r['payload']) for r in c.execute('SELECT payload FROM attachments WHERE resource_id=? AND deleted=0 ORDER BY rowid',(item['id'],))]
        return item
    def _read_many(self,c,rows):
        rows=list(rows)
        if not rows:return []
        grouped={r['id']:[] for r in rows}
        if len(rows)>500:
            assets=c.execute('SELECT resource_id,payload FROM attachments WHERE deleted=0 ORDER BY rowid')
            for a in assets:
                if a['resource_id'] in grouped:grouped[a['resource_id']].append(json.loads(a['payload']))
        else:
            for a in c.execute('SELECT resource_id,payload FROM attachments WHERE deleted=0 AND resource_id IN ('+','.join('?'*len(rows))+') ORDER BY rowid',list(grouped)):
                grouped[a['resource_id']].append(json.loads(a['payload']))
        return [{**json.loads(r['payload']),'deleted':bool(r['deleted']),'attachments':grouped[r['id']]} for r in rows]
    def _get_many(self,c,ids,active=False):
        rows=[]
        for start in range(0,len(ids),500):
            chunk=ids[start:start+500]
            rows.extend(c.execute('SELECT * FROM resources WHERE id IN ('+','.join('?'*len(chunk))+')',chunk).fetchall())
        if len(rows)!=len(ids) or active and any(r['deleted'] for r in rows):raise ValueError('资源不存在或已在回收站。')
        items={r['id']:r for r in self._read_many(c,rows)}
        return [items[rid] for rid in ids]
    def _get(self,c,rid,active=False):
        row=c.execute('SELECT * FROM resources WHERE id=?',(rid,)).fetchone()
        if not row or (active and row['deleted']):raise ValueError('资源不存在或已在回收站。')
        return self._read(c,row)
    def get(self,rid):
        with self.lock,self.connect() as c:return self._get(c,rid)
    def state(self,trash=False):
        with self.lock,self.connect() as c:
            rows=self._read_many(c,c.execute('SELECT * FROM resources WHERE deleted=? ORDER BY rowid DESC',(int(trash),)).fetchall())
            return {'resources':rows,'collections':[r['name'] for r in c.execute('SELECT name FROM collections ORDER BY name')], 'smartCollections':[dict(r,id=r['id'],filters=json.loads(r['filters'])) for r in c.execute('SELECT * FROM smart_collections ORDER BY rowid')], 'collectionMeta':self._collection_meta(c),'version':3}
    def _write(self,c,raw,existing=None,apply_auto=True):
        item=validate(raw,existing)
        if apply_auto:self._apply_auto_tags(c,item,existing)
        key=item['url'] or 'shiji:'+item['id']
        if item['parentId']:
            if item['parentId']==item['id']:raise ValueError('资源不能作为自己的来源。')
            self._get(c,item['parentId'])
        if item['coverId']:
            cover=c.execute('SELECT resource_id,payload,deleted FROM attachments WHERE id=?',(item['coverId'],)).fetchone()
            if not cover or cover['resource_id']!=item['id'] or cover['deleted'] or not json.loads(cover['payload'])['mime'].startswith('image/'):raise ValueError('封面图片不存在。')
        old=c.execute('SELECT id,deleted,payload FROM resources WHERE url=? AND id!=?',(key,item['id'])).fetchone()
        if old and (existing or not old['deleted']):raise Duplicate(old['id'])
        if old:
            # Re-collecting a trashed URL restores its existing identity and notes.
            item=validate(raw,self._get(c,old['id']));c.execute('UPDATE resources SET payload=?,deleted=0 WHERE id=?',(dump(item),item['id']))
        elif existing:c.execute('UPDATE resources SET url=?,payload=? WHERE id=?',(key,dump(item),item['id']))
        else:c.execute('INSERT INTO resources(id,url,payload) VALUES(?,?,?)',(item['id'],key,dump(item)))
        self._projects(c,item)
        if existing is None or existing.get('url')!=item['url']:self.enqueue_capture(c,item)
        self.dirty=True;return item
    def save(self,raw,rid=None):
        with self.lock,self.connect() as c:
            item=self._write(c,raw,self._get(c,rid,True) if rid else None)
            return {'resource':self._get(c,item['id'])}
    def capture_page(self,page,selection='',screenshot=None,image_url='',request_id=None):
        """Persist page, local bytes and derived tasks; never await remote images."""
        url=normalize_url(page.get('url',''));selection=text(selection,10000,'选中文字')
        image_url=normalize_url(image_url) if image_url else ''
        if request_id is not None:request_id=request_identifier(request_id)
        payload_hash=clip_fingerprint(page,selection,screenshot,image_url) if request_id else None
        written=[]
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    if request_id:
                        receipt=self._clip_receipt(c,request_id,payload_hash)
                        if receipt['status']=='saved':
                            try:current=self._get(c,receipt['resourceId'])
                            except ValueError:current=None
                            return {'resource':current,'alreadySaved':True,'contentAdded':False,'receipt':receipt}
                    row=c.execute('SELECT id,deleted FROM resources WHERE url=?',(url,)).fetchone()
                    current=self._get(c,row['id']) if row else None
                    added=False
                    if current:
                        notes=current['notes']
                        if selection and selection not in notes:
                            notes=text(notes+('\n\n—— 浏览器采集 ——\n' if notes else '')+selection,10000,'合并后的备注（请拆成独立片段）');added=True
                        if notes!=current['notes']:self._write(c,{'notes':notes},current)
                        if row['deleted']:c.execute('UPDATE resources SET deleted=0 WHERE id=?',(row['id'],));self.dirty=True
                        rid=row['id']
                    else:
                        item=self._write(c,{**page,'url':url,'notes':selection,'inbox':True});rid=item['id']
                    current=self._get(c,rid);revision=current['updatedAt']
                    if screenshot:
                        self.attach_in_transaction(c,rid,screenshot,{'name':'网页截图.png','cover':not bool(current['coverId']),'sourceUrl':url},written)
                        current=self._get(c,rid)
                        c.execute('UPDATE capture_jobs SET expected_revision=? WHERE resource_id=? AND url=? AND expected_revision=?',(current['updatedAt'],rid,url,revision))
                    if not c.execute("SELECT 1 FROM capture_jobs WHERE resource_id=? AND url=? AND kind='capture'",(rid,url)).fetchone():self.enqueue_capture(c,current)
                    if image_url:self.enqueue_capture(c,current,'asset',{'url':image_url})
                    result={'resource':current,'alreadySaved':bool(row and not row['deleted']),'contentAdded':bool(added or screenshot or image_url)}
                    if request_id:result['receipt']=self._record_clip(c,request_id,payload_hash,rid)
                if written:self.dirty=True
                return result
            except Exception:
                for path in written:path.unlink(missing_ok=True)
                self.dirty=previous_dirty
                raise
    def update_note(self,rid,body):
        rid=identifier(rid)
        if not isinstance(body,dict) or set(body)!={'kind','project','expected','value'}:raise ValueError('备注选项无效。')
        kind=body['kind'];project=body['project'];expected=body['expected'];value=body['value']
        if kind not in ('notes','project') or not isinstance(project,str) or not isinstance(expected,str) or not isinstance(value,str):raise ValueError('备注选项无效。')
        limit=10000 if kind=='notes' else 2000
        if len(expected)>limit or len(value)>limit:raise ValueError('备注最多 {} 个字符。'.format(limit))
        value=value.strip()
        if kind=='notes' and project!='':raise ValueError('资源备注不需要项目名称。')
        if kind=='project' and text(project,80,'项目名称',True)!=project:raise ValueError('项目名称无效。')
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    item=self._get(c,rid,True)
                    if kind=='project' and project not in item['projects'] and project not in item['projectNotes']:raise ValueError('项目备注已变化，请取消后重新打开。')
                    current=item['notes'] if kind=='notes' else item['projectNotes'].get(project,'')
                    if value==current:return {'resource':item,'changed':False}
                    if current!=expected:raise NoteConflict(current,item)
                    if kind=='notes':item['notes']=value
                    else:
                        item['projectNotes'][project]=value
                        c.execute('UPDATE resource_projects SET note=? WHERE resource_id=? AND name=?',(value,rid,project))
                    item['updatedAt']=now()
                    payload={k:v for k,v in item.items() if k not in ('attachments','deleted','deletedAt')}
                    c.execute('UPDATE resources SET payload=? WHERE id=?',(dump(payload),rid))
                    self.dirty=True
                    return {'resource':self._get(c,rid,True),'changed':True}
            except Exception:
                self.dirty=previous_dirty
                raise

    def remove(self,rid,restore=False):
        with self.lock,self.connect() as c:
            self._get(c,rid);self.invalidate_trash_undo([rid]);c.execute('UPDATE resources SET deleted=? WHERE id=?',(0 if restore else 1,rid));self.dirty=True
            if not restore:self.invalidate_capture(c,[rid])
            return {'ok':True}
    def batch(self,body,*,selection_revision=None,id_limit=10000):
        ids=names(body.get('ids',[]),id_limit);action=body.get('action');allowed=['tags','projects','favorite','organized','delete','restore']
        if not ids or action not in allowed:raise ValueError('请选择资源和批量操作。')
        values=names(body.get('tags' if action=='tags' else 'projects',[]),30,50 if action=='tags' else 80) if action in ('tags','projects') else []
        with self.lock,self.connect() as c:
            c.execute('BEGIN IMMEDIATE');self.check_query_revision(c,selection_revision)
            items=self._get_many(c,ids,action!='restore')
            if action in ('delete','restore'):self.invalidate_trash_undo(ids)
            if action=='delete':self.invalidate_capture(c,ids)
            for item in items:
                if action in ('delete','restore'):c.execute('UPDATE resources SET deleted=? WHERE id=?',(int(action=='delete'),item['id']))
                else:
                    existing=dict(item)
                    if action in ('tags','projects'):item[action]=list(dict.fromkeys(item[action]+values))
                    elif action=='favorite':item['favorite']=bool(body.get('value',True))
                    else:item['inbox']=False
                    self._write(c,item,existing)
            self.dirty=True;result={'changed':len(ids)}
            if action=='delete':result.update(self._receipt('trash',ids))
            return result
    def assign_tags(self,body,*,selection_revision=None,id_limit=10000):
        if not isinstance(body,dict) or set(body)!={'ids','tags','create'}:raise ValueError('标签选项无效。')
        ids=[identifier(i) for i in names(body['ids'],id_limit)]
        existing_tags=names(body['tags'],30,50);created_tags=names(body['create'],30,50)
        additions=names(list(dict.fromkeys(existing_tags+created_tags)),30,50)
        if not ids or not additions:raise ValueError('请选择资源和标签。')
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE');self.check_query_revision(c,selection_revision)
                    known={tag for row in c.execute('SELECT payload FROM resources WHERE deleted=0') for tag in json.loads(row['payload'])['tags']}
                    if any(tag not in known for tag in existing_tags):raise ValueError('标签已变化，请关闭后重新打开标签选择器。')
                    items=self._get_many(c,ids,True)
                    updates=[(item,names(list(dict.fromkeys(item['tags']+additions)),30,50)) for item in items]
                    changed=0
                    for item,combined in updates:
                        if combined==item['tags']:continue
                        self._write(c,{'tags':combined},item,apply_auto=False);changed+=1
                    return {'changed':changed,'resources':len(items),'tags':additions}
            except Exception:
                self.dirty=previous_dirty
                raise

    def rename_tag(self,old,new):
        old=text(old,50,'原标签',True);new=text(new,50,'新标签',True);changed=0
        with self.lock,self.connect() as c:
            for row in c.execute('SELECT * FROM resources').fetchall():
                item=self._read(c,row)
                if old in item['tags']:
                    item['tags']=list(dict.fromkeys(new if x==old else x for x in item['tags']));item['updatedAt']=now()
                    c.execute('UPDATE resources SET payload=? WHERE id=?',(dump({k:v for k,v in item.items() if k not in ('attachments','deleted')}),item['id']));changed+=1
            # Keep saved filters usable after renaming a tag.
            for row in c.execute('SELECT * FROM smart_collections').fetchall():
                filters=json.loads(row['filters'])
                for key in ('tags','excludeTags'):
                    if key in filters:filters[key]=list(dict.fromkeys(new if x==old else x for x in filters[key]))
                c.execute('UPDATE smart_collections SET filters=? WHERE id=?',(dump(filters),row['id']))
            for row in c.execute('SELECT name,auto_tags FROM collections').fetchall():
                tags=json.loads(row['auto_tags'])
                if old in tags:
                    tags=list(dict.fromkeys(new if x==old else x for x in tags))
                    c.execute('UPDATE collections SET auto_tags=? WHERE name=?',(dump(tags),row['name']))
            self.dirty=True
        return {'changed':changed}
    def smart(self,body,rid=None):
        name=text(body.get('name',''),80,'智能集合名称',True);filters=validate_filters(body.get('filters',{}));editing=rid is not None;rid=identifier(rid) if editing else str(uuid.uuid4())
        with self.lock,self.connect() as c:
            if editing and not c.execute('SELECT 1 FROM smart_collections WHERE id=?',(rid,)).fetchone():raise KeyError('智能集合已不存在，请刷新后重新选择。')
            c.execute('INSERT INTO smart_collections VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,filters=excluded.filters',(rid,name,dump(filters)));self.dirty=True
        return {'id':rid,'name':name,'filters':filters}
    def delete_smart(self,rid):
        with self.lock,self.connect() as c:
            row=c.execute('SELECT id,name,filters FROM smart_collections WHERE id=?',(rid,)).fetchone()
            if not row:raise ValueError('智能集合已不存在。')
            c.execute('DELETE FROM smart_collections WHERE id=?',(rid,));self.dirty=True
            return {'ok':True,**self._receipt('smart',tuple(row))}
    def export(self):
        data=self.state();return {'version':1,'schemaVersion':3,'exportedAt':now(),'resources':data['resources'],'collections':data['collections'],'collectionMeta':data['collectionMeta'],'smartCollections':data['smartCollections']}
    def import_json(self,body):
        if not isinstance(body,dict) or body.get('version')!=1 or not isinstance(body.get('resources'),list) or len(body['resources'])>10000:raise ValueError('请选择有效的资源库 JSON 备份。')
        # JSON exchanges content, not attachment bytes; clear unresolvable cover references.
        items=[validate({**raw,'coverId':'','parentId':''}) for raw in body['resources']]
        smart=[{'name':text(s.get('name',''),80,'集合名称',True),'filters':validate_filters(s.get('filters',{}))} for s in body.get('smartCollections',[])]
        collections=names(body.get('collections',[]),1000);meta=import_tree(body.get('collectionMeta',[]),collections);added=skipped=0
        with self.lock,self.connect() as c:
            self._merge_collection_meta(c,meta)
            for item in items:
                row=c.execute('SELECT id,deleted FROM resources WHERE url=?',(item['url'],)).fetchone() if item['url'] else None
                if row and not row['deleted']:skipped+=1;continue
                self._write(c,item,apply_auto=False);added+=1
            for s in smart:c.execute('INSERT OR IGNORE INTO smart_collections VALUES(?,?,?)',(str(uuid.uuid4()),s['name'],dump(s['filters'])))
        return {'added':added,'skipped':skipped}
    def token(self):
        with self.connect() as c:return c.execute('SELECT value FROM settings WHERE key="clipToken"').fetchone()[0]
    def set_link_status(self,rid,status,info):
        with self.lock,self.connect() as c:
            item=self._get(c,rid,True);item['linkStatus']=status;item['linkCheckedAt']=now();item['linkMessage']=info
            c.execute('UPDATE resources SET payload=? WHERE id=?',(dump({k:v for k,v in item.items() if k not in ('attachments','deleted')}),rid));self.dirty=True
    def attach_in_transaction(self,c,rid,raw,metadata,written):
        if not raw or len(raw)>64*1024*1024:raise ValueError('单个文件须为 1 字节至 64 MB。')
        if not isinstance(metadata,dict):raise ValueError('附件信息格式不正确。')
        aid=str(uuid.uuid4());name=text(metadata.get('name','附件'),240,'文件名称',True)
        name=re.sub(r'[\x00-\x1f/\\]','_',name)
        mime=detect_mime(raw)
        item={'id':aid,'resourceId':rid,'name':name,'mime':mime,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'createdAt':now(),'colors':palette(metadata.get('colors',[]))}
        for k,limit in [('sourceUrl',4000),('author',200),('licenseUrl',4000)]:
            item[k]=text(metadata.get(k,''),limit,k)
            if k.endswith('Url') and item[k]:item[k]=normalize_url(item[k])
        item['license']=metadata.get('license','待确认')
        if item['license'] not in LICENSES:raise ValueError('请选择有效的附件授权。')
        resource=self._get(c,rid,True)
        # Reuse only an intact same-resource copy with identical descriptive metadata.
        fields=('name','mime','size','sha256','colors','sourceUrl','author','licenseUrl','license')
        for row in c.execute('SELECT payload FROM attachments WHERE resource_id=? AND deleted=0',(rid,)):
            existing=json.loads(row['payload']);path=self.files/existing['id']
            if any(existing.get(k)!=item.get(k) for k in fields):continue
            try:identical=not path.is_symlink() and path.read_bytes()==raw
            except OSError:identical=False
            if not identical:continue
            if mime.startswith('image/') and metadata.get('cover') and resource['coverId']!=existing['id']:
                resource['coverId']=existing['id'];resource['colors']=existing['colors'];self._write(c,resource,resource)
            return {'attachment':existing,'reused':True}
        publish_file(self,c,item,raw=raw);written.append(self.files/aid)
        c.execute('INSERT INTO attachments VALUES(?,?,?,0)',(aid,rid,dump(item)))
        if mime.startswith('image/') and metadata.get('cover'):
            resource['coverId']=aid;resource['colors']=item['colors'];self._write(c,resource,resource)
        return {'attachment':item,'reused':False}
    def attachment(self,rid,raw,metadata):
        written=[]
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:result=self.attach_in_transaction(c,rid,raw,metadata,written)
                if not result['reused']:self.dirty=True
                return result
            except Exception:
                for destination in written:destination.unlink(missing_ok=True)
                self.dirty=previous_dirty
                raise
    def file(self,aid):
        with self.lock,self.connect() as c:
            row=c.execute('SELECT * FROM attachments WHERE id=?',(aid,)).fetchone()
            if not row or row['deleted']:raise ValueError('附件不存在。')
            item=json.loads(row['payload']);path=self.files/aid
            if not path.is_file():raise ValueError('文件缺失，请从完整备份恢复。')
            return item,path
    def update_attachment(self,aid,raw):
        with self.lock,self.connect() as c:
            row=c.execute('SELECT * FROM attachments WHERE id=? AND deleted=0',(aid,)).fetchone()
            if not row:raise ValueError('附件不存在。')
            self._get(c,row['resource_id'],True);item=json.loads(row['payload'])
            for k,limit in [('author',200),('sourceUrl',4000),('licenseUrl',4000)]:
                if k in raw:
                    item[k]=text(raw[k],limit,k)
                    if k.endswith('Url') and item[k]:item[k]=normalize_url(item[k])
            if 'license' in raw:
                if raw['license'] not in LICENSES:raise ValueError('请选择有效的附件授权。')
                item['license']=raw['license']
            if 'colors' in raw:item['colors']=palette(raw['colors'])
            c.execute('UPDATE attachments SET payload=? WHERE id=?',(dump(item),aid))
            resource=self._get(c,row['resource_id'])
            if resource['coverId']==aid:
                resource['colors']=item['colors'];self._write(c,resource,resource)
            self.dirty=True
        return {'attachment':item}
    @property
    def dirty(self):return self._dirty
    @dirty.setter
    def dirty(self,value):
        self._dirty=value
        if value:self._change_generation+=1
    def start_auto_backup(self):
        if getattr(self,'_auto_backup_thread',None) and self._auto_backup_thread.is_alive():return
        self._auto_backup_stop=threading.Event()
        def worker():
            from datetime import date
            last_zip=date.today()
            while not self._auto_backup_stop.is_set():
                try:
                    if self.dirty or not self.backup_list()['snapshots']:self.create_snapshot()
                    if date.today()!=last_zip:self.create_backup();last_zip=date.today()
                    self.prune_backups()
                except (OSError,ValueError,sqlite3.Error):self.dirty=True
                if self._auto_backup_stop.wait(60):break
        self._auto_backup_thread=threading.Thread(target=worker,daemon=True);self._auto_backup_thread.start()
    def stop_auto_backup(self):
        if hasattr(self,'_auto_backup_stop'):
            self._auto_backup_stop.set();self._auto_backup_thread.join(timeout=5)

def detect_mime(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):return 'image/png'
    if raw.startswith(b'\xff\xd8\xff'):return 'image/jpeg'
    if raw[:6] in (b'GIF87a',b'GIF89a'):return 'image/gif'
    if raw.startswith(b'RIFF') and raw[8:12]==b'WEBP':return 'image/webp'
    if raw.startswith(b'RIFF') and raw[8:12]==b'WAVE':return 'audio/wav'
    if raw.startswith(b'fLaC'):return 'audio/flac'
    if raw.startswith(b'OggS'):return 'audio/ogg'
    if raw.startswith(b'ID3') or (len(raw)>1 and raw[0]==255 and raw[1]&0xe0==0xe0):return 'audio/mpeg'
    if len(raw)>12 and raw[4:8]==b'ftyp':return 'video/mp4'
    if raw.startswith(b'\x1aE\xdf\xa3'):return 'video/webm'
    return 'application/octet-stream'
