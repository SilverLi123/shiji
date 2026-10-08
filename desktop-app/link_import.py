"""Bulk URL intake with a read-only preview and an atomic selected import."""
import re
from urllib.parse import urlsplit

class LinkImportOperations:
    def preview_links(self,body):
        from storage import text,normalize_url
        raw=text(body.get('text',''),128000,'网址列表',True);lines=[line.strip() for line in raw.splitlines() if line.strip()]
        if len(lines)>200:raise ValueError('一次最多粘贴 200 个网址。')
        with self.lock,self.connect() as c:known={r['url']:r for r in c.execute('SELECT id,url,deleted FROM resources')}
        seen=set();items=[]
        for i,line in enumerate(lines,1):
            title='';url=line;item={'line':i,'input':line,'url':'','title':'','status':'invalid','message':'','existingId':''}
            match=re.fullmatch(r'\[([^\]]{1,200})\]\((https?://[^\s)]+)\)',line)
            if match:title,url=match.groups()
            try:
                url=normalize_url(url);title=text(title or urlsplit(url).hostname,200,'名称',True)
                if url in seen:status='duplicate';message='列表内重复'
                elif url in known:status='trash' if known[url]['deleted'] else 'existing';message='已在回收站，可前往恢复' if status=='trash' else '已收藏'
                else:status='new';message='可以导入'
                seen.add(url);item.update(url=url,title=title,status=status,message=message,existingId=known[url]['id'] if url in known else '')
            except ValueError as e:item['message']=str(e)
            items.append(item)
        return {'items':items,'new':sum(p['status']=='new' for p in items),'total':len(items)}
    def import_links(self,body):
        from storage import validate,names
        source=body.get('items')
        if not isinstance(source,list) or not source or len(source)>200 or any(not isinstance(r,dict) for r in source):raise ValueError('一次请选择 1 至 200 个网址。')
        tags=names(body.get('tags',[]),30,50);projects=names(body.get('projects',[]));category=body.get('category','其他')
        items=[validate({'url':r.get('url',''),'title':r.get('title',''),'tags':tags,'projects':projects,'category':category,'inbox':True}) for r in source]
        added=[];skipped=[]
        with self.lock,self.connect() as c:
            for item in items:
                row=c.execute('SELECT id,deleted FROM resources WHERE url=?',(item['url'],)).fetchone()
                if row:skipped.append({'url':item['url'],'id':row['id'],'status':'trash' if row['deleted'] else 'existing'});continue
                saved=self._write(c,item);added.append(saved['id'])
        return {'added':len(added),'skipped':len(skipped),'ids':added,'skippedItems':skipped}
