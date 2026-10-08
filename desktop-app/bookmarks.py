"""Parse bookmark exports as text; preview first, commit selected items atomically."""
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit

MAX_HTML=5*1024*1024
MAX_BOOKMARKS=2000

class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.pending=None;self.capture=None;self.parts=[];self.attrs={}
        self.items=[];self.description=None;self.description_target=None;self.dd=[];self.ignored=0;self.saw_dl=False
    def finish_description(self):
        if self.description is not None:self.items[self.description]['notes']=' '.join(''.join(self.dd).split())
        self.description=None;self.dd=[]
    def finish_capture(self):
        if self.capture=='h3':
            self.description_target=None
            value=' '.join(''.join(self.parts).split()) or '未命名文件夹'
            if len(value)>200:raise ValueError('书签文件夹名称超过 200 字，请先在浏览器中缩短后重新导出。')
            self.pending=value
        elif self.capture=='a':
            if len(self.items)>=MAX_BOOKMARKS:raise ValueError('一次最多导入 2000 条书签，请分批导出。')
            self.items.append({'line':len(self.items)+1,'url':self.attrs.get('href',''),'title':' '.join(''.join(self.parts).split()),'folders':[p for p in self.stack if p is not None],'notes':'','tags':self.attrs.get('tags',''),'date':self.attrs.get('add_date','')})
            self.description_target=len(self.items)-1
        self.capture=None;self.parts=[];self.attrs={}
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.ignored+=1;return
        if self.ignored:return
        if tag in ('dt','h3','a','dl'):self.finish_description()
        if tag in ('h3','a'):
            self.finish_capture();self.capture=tag;self.parts=[];self.attrs=dict(attrs)
            if tag=='a':self.pending=None
        elif tag=='dl':
            self.saw_dl=True;self.finish_capture();self.description_target=None;self.stack.append(self.pending);self.pending=None
            if len(self.stack)>50:raise ValueError('书签文件夹层级过深，请先整理后重新导出。')
        elif tag=='dd':
            self.finish_capture();self.finish_description()
            self.description=self.description_target
        elif tag in ('br','p'):
            if self.description is not None:self.dd.append(' ')
            elif self.capture:self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('script','style'):
            self.ignored=max(0,self.ignored-1);return
        if self.ignored:return
        if tag==self.capture:self.finish_capture()
        if tag=='dd':self.finish_description()
        if tag=='dl':
            self.finish_capture();self.finish_description()
            self.description_target=None
            if self.stack:self.stack.pop()
            self.pending=None
    def handle_data(self,data):
        if self.ignored:return
        if self.capture:self.parts.append(data)
        elif self.description is not None:self.dd.append(data)

def parse_bookmarks(raw):
    from storage import text,normalize_url
    raw=text(raw,MAX_HTML,'书签 HTML',True)
    if len(raw.encode('utf-8'))>MAX_HTML:raise ValueError('书签 HTML 文件最多 5 MB。')
    parser=BookmarkParser();parser.feed(raw);parser.close();parser.finish_capture();parser.finish_description()
    if not parser.saw_dl or not parser.items:raise ValueError('没有找到浏览器书签。请选择浏览器导出的标准 HTML 书签文件。')
    for item in parser.items:
        warnings=[];item['valid']=True
        try:
            if urlsplit(item['url']).scheme.lower() not in ('http','https'):raise ValueError('只导入完整的 HTTP/HTTPS 网页网址。')
            item['url']=normalize_url(item['url'])
        except ValueError as e:item['valid']=False;item['error']=str(e)
        item['title']=item['title'] or (urlsplit(item['url']).hostname if item['valid'] else '') or '无标题书签'
        if len(item['title'])>200:item['title']=item['title'][:200];warnings.append('原标题超过 200 字，已缩短，可修改')
        tags=list(dict.fromkeys(t.strip() for t in item['tags'].split(',') if t.strip()))
        if any(len(t)>50 for t in tags) or len(tags)>30:warnings.append('标签超过限制，已缩短至每个 50 字、最多 30 个')
        item['tags']=list(dict.fromkeys(t[:50] for t in tags))[:30]
        if len(item['notes'])>10000:item['notes']=item['notes'][:10000];warnings.append('描述超过 10000 字，已缩短')
        item['createdAt']=''
        if item['date']:
            try:
                value=int(item['date'])
                if value<0:raise ValueError()
                item['createdAt']=datetime.fromtimestamp(value,timezone.utc).isoformat()
            except (ValueError,OverflowError,OSError):warnings.append('原收藏时间无效，将使用导入时间')
        item['warnings']=warnings;item.pop('date')
    return raw,parser.items

def available_name(base,used):
    base=re.sub(r'[,，、\x00-\x1f\x7f]',' ',base).strip() or '未命名文件夹'
    base=' '.join(base.split())[:80];name=base;n=2
    while name in used:
        suffix='（'+str(n)+'）';name=base[:80-len(suffix)]+suffix;n+=1
    used.add(name);return name

class BookmarkOperations:
    def _bookmark_plan(self,c,body):
        from storage import text
        raw,items=parse_bookmarks(body.get('html',''))
        preserve=body.get('preserveFolders',True)
        if not isinstance(preserve,bool):raise ValueError('文件夹选项无效。')
        root=text(body.get('rootName','浏览器书签'),80,'根项目名称',True)
        if any(ch in root for ch in ',，、\n\r'):raise ValueError('根项目名称不能包含逗号、顿号或换行。')
        current=self._collection_meta(c)
        rows=[dict(r) for r in c.execute('SELECT id,url,deleted FROM resources ORDER BY id')]
        token=hashlib.sha256(json.dumps([raw,preserve,root,current,rows],sort_keys=True).encode()).hexdigest()
        known={r['url']:r for r in rows};first={}
        for item in items:
            item['folderPaths']=[item['folders']];item['existingId']=''
            if not item['valid']:item.update(status='invalid',message=item['error']);continue
            url=item['url']
            if url in first:
                owner=first[url];item.update(status='duplicate',message='文件内重复，将随第一条保留文件夹归属')
                if item['folders'] not in owner['folderPaths']:owner['folderPaths'].append(item['folders'])
                extra=[t for t in item['tags'] if t not in owner['tags']]
                if len(owner['tags'])+len(extra)>30:owner['warnings'].append('重复项合并标签超过 30 个，仅保留前 30 个')
                owner['tags']=(owner['tags']+extra)[:30]
                if item['notes'] and item['notes']!=owner['notes']:
                    merged=owner['notes']+('\n\n' if owner['notes'] else '')+item['notes']
                    if len(merged)>10000:owner['warnings'].append('重复项合并描述超过 10000 字，已缩短')
                    owner['notes']=merged[:10000]
                owner['warnings']+=item['warnings'];continue
            first[url]=item
            if url in known:
                record=known[url];item.update(status='trash' if record['deleted'] else 'existing',message='已在回收站，可前往恢复' if record['deleted'] else '已收藏，保留原内容',existingId=record['id'])
            else:item.update(status='new',message='可以导入')
        used={p['name'] for p in current};root_actual=available_name(root,used)
        planned=[{'name':root_actual,'parent':'','autoTags':[],'archived':False}];mapping={():root_actual}
        for item in items:
            item['projects']=[];item['projectPaths']=[]
            if item['status']!='new':continue
            paths=item['folderPaths'] if preserve else [[]]
            if preserve and (any(len(p)>9 for p in paths) or len(paths)>30):
                item.update(status='invalid',message='文件夹超过九层或归属超过 30 个，请返回并取消保留文件夹');continue
            for path in paths:
                previous=()
                for part in path:
                    current_path=previous+(part,)
                    if current_path not in mapping:
                        name=available_name(part,used);mapping[current_path]=name
                        planned.append({'name':name,'parent':mapping[previous],'autoTags':[],'archived':False})
                    previous=current_path
                project=mapping[previous]
                if project not in item['projects']:
                    item['projects'].append(project)
                    item['projectPaths'].append(' / '.join(mapping[tuple(path[:i])] for i in range(len(path)+1)))
        return {'items':items,'total':len(items),'new':sum(i['status']=='new' for i in items),'rootName':root_actual,'planToken':token,'projects':planned,'preserveFolders':preserve}
    def preview_bookmarks(self,body):
        with self.lock,self.connect() as c:return self._bookmark_plan(c,body)
    def import_bookmarks(self,body):
        from storage import validate,names
        chosen=body.get('items')
        if not isinstance(chosen,list) or not chosen or len(chosen)>MAX_BOOKMARKS or any(not isinstance(i,dict) or type(i.get('line')) is not int for i in chosen):raise ValueError('请选择有效的书签条目。')
        lines=[i['line'] for i in chosen]
        if len(set(lines))!=len(lines):raise ValueError('导入条目重复。')
        tags=names(body.get('tags',[]),30,50)
        with self.lock,self.connect() as c:
            plan=self._bookmark_plan(c,body)
            if body.get('planToken')!=plan['planToken']:raise ValueError('收藏或项目已变化，请返回并重新预览书签。')
            rows={i['line']:i for i in plan['items']};prepared=[];needed=set()
            for selected in chosen:
                item=rows.get(selected['line'])
                if not item or item['status']!='new':raise ValueError('只能导入预览中的新网址，请重新选择。')
                raw={'url':item['url'],'title':selected.get('title',item['title']),'notes':item['notes'],'tags':list(dict.fromkeys(item['tags']+tags)),'projects':item['projects'],'inbox':True}
                if item['createdAt']:raw['createdAt']=item['createdAt']
                prepared.append(validate(raw));needed.update(item['projects'])
            parents={p['name']:p['parent'] for p in plan['projects']}
            for name in list(needed):
                while name:
                    needed.add(name);name=parents.get(name,'')
            self._merge_collection_meta(c,[p for p in plan['projects'] if p['name'] in needed])
            ids=[self._write(c,item)['id'] for item in prepared]
        return {'added':len(ids),'ids':ids,'rootName':plan['rootName'],'createdProjects':len(needed)}
