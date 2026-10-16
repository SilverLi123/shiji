"""Bounded, revision-consistent queries over disposable local search documents."""
import copy
import base64
import hashlib
import hmac
import json
import math
import secrets
import sqlite3
from search_text import parse_terms,gram_query,highlight_ranges

class QueryConflict(ValueError):pass

def color_distance(a,b):
    def lab(h):
        v=[int(h[i:i+2],16)/255 for i in (1,3,5)];r,g,b=[((x+.055)/1.055)**2.4 if x>.04045 else x/12.92 for x in v]
        xyz=[(r*.4124+g*.3576+b*.1805)/.95047,r*.2126+g*.7152+b*.0722,(r*.0193+g*.1192+b*.9505)/1.08883]
        x,y,z=[v**(1/3) if v>.008856 else 7.787*v+16/116 for v in xyz];return (116*y-16,500*(x-y),200*(y-z))
    try:return math.sqrt(sum((x-y)**2 for x,y in zip(lab(a),lab(b))))
    except (TypeError,ValueError):return 1000

def summary(item,terms=(),media=False):
    out=dict(item);out['_summary']=True;out['attachmentCount']=len(item['attachments'])
    cover=item.get('coverId');assets=item['attachments'][:8]
    if cover and not any(a['id']==cover for a in assets):assets+= [a for a in item['attachments'] if a['id']==cover]
    out['attachments']=item['attachments'] if media else assets
    out['_highlights']={'title':highlight_ranges(item['title'],terms)}
    excerpt=''
    for key in ('description','notes','snippet'):
        value=item.get(key,'');lower=value.lower();positions=[lower.find(t) for t in terms if t in lower]
        if positions:
            start=max(0,min(positions)-50);excerpt=value[start:start+240];break
    out['_excerpt']=excerpt;out['_highlights']['excerpt']=highlight_ranges(excerpt,terms)
    for key,n in (('description',320),('notes',240),('snippet',1600)):out[key]=item.get(key,'')[:n]
    out['snippet']='\n'.join(line[:160] for line in item.get('snippet','').split('\n')[:9])
    out['projectNotes']={k:v[:160] for k,v in item.get('projectNotes',{}).items() if k in item.get('projects',[])}
    return out

class QueryOperations:
    def _revision(self,c):return int(c.execute("SELECT value FROM search_meta WHERE key='revision'").fetchone()[0])
    def check_query_revision(self,c,revision):
        if revision is not None and (type(revision) is not int or self._revision(c)!=revision):raise QueryConflict('资源库已变化，请刷新匹配范围后重试。')
    def _query_context(self,body,c):
        from storage import validate_filters
        if not isinstance(body,dict):raise ValueError('查询格式不正确。')
        from storage import text
        text(body.get('scopeValue',''),80,'查询范围')
        scope=body.get('scope','all')
        if scope not in ('all','trash','favorite','inbox','assets','snippets','category','collection','smart','health'):raise ValueError('查询范围无效。')
        raw=body.get('filters',{})
        if not isinstance(raw,dict):raise ValueError('筛选格式不正确。')
        if scope=='smart':
            row=c.execute('SELECT filters FROM smart_collections WHERE id=?',(body.get('scopeValue',''),)).fetchone()
            if not row:raise ValueError('智能集合不存在。')
            if 'filters' not in body:raw=json.loads(row[0])
        if scope in ('category','collection') and 'filters' not in body and body.get('scopeValue'):raw={**raw,scope:body['scopeValue']}
        f=validate_filters(raw);terms=parse_terms(f['search']);params=[int(scope=='trash')];conditions=['d.deleted=?']
        join=''
        if self._fts_ready(c) and terms:
            conditions.append('d.rowid IN (SELECT rowid FROM search_fts WHERE search_fts MATCH ?)');params.append(gram_query(terms))
        for term in terms:conditions.append('instr(d.text,?)>0');params.append(term)
        for key,col in (('category','category'),('kind','kind'),('price','price'),('license','license'),('linkStatus','link_status')):
            if f[key]:conditions.append('d.'+col+'=?');params.append(f[key])
        for key in ('favorite','inbox'):
            if scope==key:conditions.append('d.'+key+'=1')
            if key in f:conditions.append('d.'+key+'=?');params.append(int(f[key]))
        if scope=='assets' or f.get('hasAssets'):conditions.append("(d.kind='file' OR d.asset_count>0)")
        if scope=='snippets' or f.get('isSnippet'):conditions.append("d.kind IN ('code','prompt')")
        if f.get('collection'):
            meta=self._collection_meta(c);branch={f['collection']}
            for _ in range(11):branch.update(p['name'] for p in meta if p['parent'] in branch)
            conditions.append('EXISTS(SELECT 1 FROM json_each(d.projects) WHERE value IN ('+','.join('?'*len(branch))+'))');params+=sorted(branch)
        if f['tags']:
            if f['tagMode']=='any':conditions.append('EXISTS(SELECT 1 FROM json_each(d.tags) WHERE value IN ('+','.join('?'*len(f['tags']))+'))');params+=f['tags']
            else:
                for tag in f['tags']:conditions.append('EXISTS(SELECT 1 FROM json_each(d.tags) WHERE value=?)');params.append(tag)
        for tag in f['excludeTags']:conditions.append('NOT EXISTS(SELECT 1 FROM json_each(d.tags) WHERE value=?)');params.append(tag)
        for key,col in (('noTags','tags'),('noProjects','projects')):
            if f[key]:conditions.append('json_array_length(d.'+col+')=0')
        if f['hasNotes']:conditions.append('d.has_notes=1')
        if f['mediaType']:conditions.append('EXISTS(SELECT 1 FROM json_each(d.media) WHERE value=?)');params.append(f['mediaType'])
        if f['domain']:
            conditions.append('(d.domain=?'+(' OR d.domain LIKE ?' if f['includeSubdomains'] else '')+')');params.append(f['domain'])
            if f['includeSubdomains']:params.append('%.'+f['domain'])
        for key,op in (('createdFrom','>='),('createdTo','<=')):
            if f[key]:conditions.append("(d.created_day!='' AND d.created_day"+op+'?)');params.append(f[key])
        if f['color']:conditions.append('EXISTS(SELECT 1 FROM json_each(d.colors) WHERE color_distance(value,?)<32)');params.append(f['color'])
        if body.get('mediaOnly'):
            conditions.append("(EXISTS(SELECT 1 FROM attachments a WHERE a.resource_id=d.id AND a.deleted=0 AND (json_extract(a.payload,'$.mime') LIKE 'image/%' OR json_extract(a.payload,'$.mime') LIKE 'audio/%' OR json_extract(a.payload,'$.mime') LIKE 'video/%')) OR EXISTS(SELECT 1 FROM resources r WHERE r.id=d.id AND (coalesce(json_extract(r.payload,'$.thumbnail'),'')!='' OR r.url IN ('https://polyhaven.com/','https://www.polyhaven.com/','https://freesound.org/','https://reactbits.dev/','https://motionsites.ai/','https://www.recent.co/','https://recent.co/'))))")
        sort=body.get('sort','relevance' if terms else 'new')
        if sort not in ('new','updated','name','relevance'):raise ValueError('排序方式无效。')
        # Title matches dominate; exact phrase > prefix > contains; every term is literal.
        rank='0';rankparams=[]
        if terms:
            rank='+'.join('(CASE WHEN d.title=? THEN 100 WHEN instr(d.title,?)=1 THEN 40 WHEN instr(d.title,?)>0 THEN 20 ELSE 0 END)' for _ in terms)
            for t in terms:rankparams += [t,t,t]
        ordering=('score DESC,d.created_at DESC,d.id' if sort=='relevance' else 'd.title,d.id' if sort=='name' else 'd.'+('updated_at' if sort=='updated' else 'created_at')+' DESC,d.id')
        fingerprint=hashlib.sha256(json.dumps([scope,f,sort,bool(body.get('mediaOnly'))],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        return {'from':' FROM search_docs d'+(' NOT INDEXED' if self._fts_ready(c) and terms else '')+join,'where':' WHERE '+' AND '.join(conditions),'params':params,'rank':rank,'rankparams':rankparams,'order':ordering,'terms':terms,'fingerprint':fingerprint}

    def _cursor(self,value=None):
        if not hasattr(self,'_cursor_key'):self._cursor_key=secrets.token_bytes(32)
        if isinstance(value,dict):
            raw=json.dumps(value,separators=(',',':')).encode();return base64.urlsafe_b64encode(raw+hmac.digest(self._cursor_key,raw,'sha256')).decode()
        try:
            if not isinstance(value,str) or len(value)>1000:raise ValueError()
            raw=base64.b64decode(value,altchars=b'-_',validate=True);content,signature=raw[:-32],raw[-32:]
            if not hmac.compare_digest(signature,hmac.digest(self._cursor_key,content,'sha256')):raise ValueError()
            return json.loads(content)
        except (ValueError,TypeError):raise ValueError('分页凭据无效，请重新查询。')

    def _with_query(self,callback):
        # Keep writes and query snapshot consistent, including external raw-SQL writers.
        for attempt in range(3):
            try:
                self.flush_search(wait_fts=False)
                with self.lock,self.connect() as c:
                    c.execute('BEGIN')
                    if c.execute('SELECT 1 FROM search_dirty LIMIT 1').fetchone():continue
                    return callback(c)
            except sqlite3.DatabaseError as e:
                # Only derived-table failures may be repaired. Canonical DB errors propagate.
                if attempt or not self.search_damage_repairable():raise
                with self.lock,self.connect() as c:self._search_schema(c)
                self.rebuild_search(wait_fts=False)
        raise QueryConflict('资源正在更新，请稍后重新查询。')

    def query_resources(self,body):
        def query(c):
            q=self._query_context(body,c);limit=body.get('limit',60)
            if type(limit) is not int or not 1<=limit<=100:raise ValueError('每页须为 1 至 100 条。')
            rev=self._revision(c);offset=0
            if body.get('cursor'):
                cursor=self._cursor(body['cursor'])
                if cursor.get('revision')!=rev or cursor.get('query')!=q['fingerprint']:raise QueryConflict('查询或资源库已变化，请从第一页重新加载。')
                offset=cursor['offset']
            cache=getattr(self,'_query_counts',{});cachekey=(rev,q['fingerprint'])
            groups=cache.get(cachekey)
            if groups is None:
                groups={r[0]:r[1] for r in c.execute('SELECT d.kind,count(*)'+q['from']+q['where']+' GROUP BY d.kind',q['params'])}
                if len(cache)>=32:cache.clear()
                cache[cachekey]=groups;self._query_counts=cache
            total=sum(groups.values())
            if body.get('edge')=='last' and not body.get('cursor'):offset=max(0,((total-1)//limit)*limit)
            if body.get('anchor') and not body.get('cursor'):
                from storage import identifier
                anchor=identifier(body['anchor'])
                ordering=q['order'].replace('d.','')
                sql='WITH candidates AS (SELECT d.id,d.title,d.created_at,d.updated_at,'+q['rank']+' AS score'+q['from']+q['where']+'), numbered AS (SELECT id,row_number() OVER (ORDER BY '+ordering+') AS position FROM candidates) SELECT position FROM numbered WHERE id=?'
                position=c.execute(sql,q['rankparams']+q['params']+[anchor]).fetchone()
                if not position:raise QueryConflict('资源不在当前匹配范围中，请重新打开预览。')
                offset=((position[0]-1)//limit)*limit
            rows=c.execute('SELECT d.id,'+q['rank']+' AS score'+q['from']+q['where']+' ORDER BY '+q['order']+' LIMIT ? OFFSET ?',q['rankparams']+q['params']+[limit,offset]).fetchall()
            ids=[r['id'] for r in rows]
            resources=self._summaries(c,ids,q['terms'],media=body.get('projection')=='media')
            cursor=self._cursor({'revision':rev,'query':q['fingerprint'],'offset':offset+len(ids)}) if offset+len(ids)<total else None
            return {'resources':resources,'total':total,'revision':rev,'nextCursor':cursor,'previousCursor':self._cursor({'revision':rev,'query':q['fingerprint'],'offset':max(0,offset-limit)}) if offset else None,'terms':q['terms'],'kindCounts':groups}
        return self._with_query(query)

    def _summaries(self,c,ids,terms=(),media=False):
        if not ids:return []
        rows=c.execute('SELECT * FROM resources WHERE id IN ('+','.join('?'*len(ids))+')',ids).fetchall()
        items={r['id']:summary(r,terms,media=media) for r in self._read_many(c,rows)}
        return [items[rid] for rid in ids if rid in items]

    def query_ids(self,body):
        def query(c):
            q=self._query_context(body,c)
            if body.get('linksOnly'):q['where']+=" AND d.domain!=''"
            rows=c.execute('SELECT d.id'+q['from']+q['where']+' ORDER BY d.id LIMIT 100001',q['params']).fetchall()
            if len(rows)>100000:raise ValueError('匹配结果超过十万条，请缩小范围。')
            return {'ids':[r[0] for r in rows],'revision':self._revision(c)}
        return self._with_query(query)

    def resource_summaries(self,body):
        from storage import names,identifier
        ids=[identifier(x) for x in names(body.get('ids',[]),500)]
        with self.lock,self.connect() as c:return {'resources':self._summaries(c,ids,media=body.get('projection')=='media')}

    def library_metadata(self):
        def metadata(c):
            revision=self._revision(c)
            if getattr(self,'_library_meta',{}).get('revision')==revision:
                cached=copy.deepcopy(self._library_meta);cached['search']=self.search_capabilities();return cached
            counts={k:0 for k in ('all','trash','favorite','inbox','assets','snippets')}
            row=c.execute("SELECT sum(deleted=0),sum(deleted=1),sum(deleted=0 AND favorite=1),sum(deleted=0 AND inbox=1),sum(deleted=0 AND (kind='file' OR asset_count>0)),sum(deleted=0 AND kind IN ('code','prompt')) FROM search_docs").fetchone()
            counts.update(zip(counts,(x or 0 for x in row)))
            categories={r[0]:r[1] for r in c.execute('SELECT category,count(*) FROM search_docs WHERE deleted=0 GROUP BY category')}
            tags={r[0]:r[1] for r in c.execute('SELECT j.value,count(*) FROM search_docs d,json_each(d.tags) j WHERE d.deleted=0 GROUP BY j.value')}
            alltags=[r[0] for r in c.execute('SELECT DISTINCT j.value FROM search_docs d,json_each(d.tags) j ORDER BY j.value')]
            meta=self._collection_meta(c);projects={p['name']:0 for p in meta}
            # Distinct ancestor memberships avoid double counting multi-project resources.
            rows=c.execute("WITH RECURSIVE ancestors(name,parent) AS (SELECT name,name FROM collections UNION SELECT a.name,c.parent FROM ancestors a JOIN collections c ON c.name=a.parent WHERE c.parent!='') SELECT a.parent,count(DISTINCT d.id) FROM search_docs d,json_each(d.projects) j JOIN ancestors a ON a.name=j.value WHERE d.deleted=0 GROUP BY a.parent")
            projects.update({r[0]:r[1] for r in rows})
            smart=[dict(r,filters=json.loads(r['filters'])) for r in c.execute('SELECT * FROM smart_collections ORDER BY rowid')]
            smartcounts={}
            for s in smart:
                q=self._query_context({'filters':s['filters']},c);smartcounts[s['id']]=c.execute('SELECT count(*)'+q['from']+q['where'],q['params']).fetchone()[0]
            result={'queryVersion':1,'version':3,'revision':self._revision(c),'search':self.search_capabilities(),'counts':counts,'categoryCounts':categories,'tagCounts':tags,'allTags':alltags,'projectCounts':projects,'smartCounts':smartcounts,'collections':[p['name'] for p in meta],'collectionMeta':meta,'smartCollections':smart}
            self._library_meta=result;return copy.deepcopy(result)
        return self._with_query(metadata)

    def resource_lookup(self,body):
        from storage import normalize_url
        url=normalize_url(body.get('url',''))
        with self.lock,self.connect() as c:
            row=c.execute('SELECT * FROM resources WHERE url=? AND deleted=0',(url,)).fetchone()
            return {'resource':self._read(c,row) if row else None}

    def resource_detail(self,rid):
        def query(c):
            item=self._get(c,rid)
            related=[dict(r) for r in c.execute("SELECT d.id,json_extract(r.payload,'$.title') AS title FROM search_docs d JOIN resources r ON r.id=d.id WHERE d.deleted=0 AND d.parent_id=? ORDER BY d.title,d.id",(rid,))]
            # Canonical title case is read only for this bounded relationship set.
            if item.get('parentId'):
                parent=c.execute('SELECT id,payload FROM resources WHERE id=?',(item['parentId'],)).fetchone()
                parent={'id':parent['id'],'title':json.loads(parent['payload'])['title']} if parent else None
            else:parent=None
            return {'resource':item,'parent':parent,'children':related}
        return self._with_query(query)

    def organization_context(self,body):
        from storage import names,identifier
        ids=[identifier(x) for x in names(body.get('ids',[]),100000)]
        def query(c):
            self.check_query_revision(c,body.get('revision'))
            items=[]
            for start in range(0,len(ids),500):
                chunk=ids[start:start+500]
                items += [{'id':r['id'],'tags':json.loads(r['tags']),'projects':json.loads(r['projects'])} for r in c.execute('SELECT id,tags,projects FROM search_docs WHERE deleted=0 AND id IN ('+','.join('?'*len(chunk))+')',chunk)]
            tags={r[0]:r[1] for r in c.execute('SELECT j.value,count(*) FROM search_docs d,json_each(d.tags) j WHERE deleted=0 GROUP BY j.value')}
            return {'resources':items,'tagCounts':tags,'collectionMeta':self._collection_meta(c),'revision':self._revision(c)}
        return self._with_query(query)

    def query_batch(self,body):
        if type(body.get('revision')) is not int:raise ValueError('请选择最新匹配范围。')
        operation=body.get('operation');method={'batch':self.batch,'tags':self.assign_tags,'projects':self.assign_projects,'removeProjects':self.remove_projects}.get(operation)
        if not method or not isinstance(body.get('body'),dict):raise ValueError('批量操作无效。')
        return method(body['body'],selection_revision=body['revision'],id_limit=100000)
