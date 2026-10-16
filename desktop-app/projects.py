"""Project trees and inherited tagging. Names remain compatible with v2 projects."""
import json
import sqlite3

def validate_tree(records):
    from storage import text,names
    if not isinstance(records,list) or len(records)>1000:raise ValueError('项目结构过大或格式不正确。')
    result=[];known=set()
    for raw in records:
        if not isinstance(raw,dict):raise ValueError('项目结构格式不正确。')
        name=text(raw.get('name',''),80,'项目名称',True);parent=text(raw.get('parent',''),80,'上级项目')
        if name in known:raise ValueError('项目名称重复。')
        archived=raw.get('archived',False)
        if not isinstance(archived,bool):raise ValueError('归档状态无效。')
        known.add(name);result.append({'name':name,'parent':parent,'autoTags':names(raw.get('autoTags',[]),30,50),'archived':archived})
    parents={p['name']:p['parent'] for p in result}
    for p in result:
        current=p['name'];seen=set()
        while current:
            if current not in parents:raise ValueError('上级项目不存在。')
            if current in seen:raise ValueError('不能把项目放入自己或自己的下级中。')
            seen.add(current)
            if len(seen)>10:raise ValueError('项目最多支持十层。')
            current=parents[current]
    return result

def import_tree(records,collections):
    if not isinstance(records,list):raise ValueError('项目结构格式不正确。')
    present={p.get('name') for p in records if isinstance(p,dict)}
    return validate_tree(records+[{'name':n} for n in collections if n not in present])

class ProjectOperations:
    def _collection_meta(self,c):
        return [{'name':r['name'],'parent':r['parent'],'autoTags':json.loads(r['auto_tags']),'archived':bool(r['archived'])} for r in c.execute('SELECT * FROM collections ORDER BY name')]
    def _merge_collection_meta(self,c,records):
        current=self._collection_meta(c);known={p['name'] for p in current}
        additions=[p for p in records if p['name'] not in known]
        validate_tree(current+additions)
        for p in additions:c.execute('INSERT INTO collections(name,parent,auto_tags,archived) VALUES(?,?,?,?)',(p['name'],p['parent'],json.dumps(p['autoTags'],ensure_ascii=False),int(p['archived'])))
    def _apply_auto_tags(self,c,item,existing=None):
        from storage import names
        old=set((existing or {}).get('projects',[]));meta={p['name']:p for p in self._collection_meta(c)};tags=list(item['tags'])
        for name in item['projects']:
            if name in old:continue
            seen=set()
            while name and name in meta and name not in seen:
                seen.add(name);tags+=meta[name]['autoTags'];name=meta[name]['parent']
        item['tags']=names(list(dict.fromkeys(tags)),30,50)
        return item
    def collection(self,name,parent='',auto_tags=None):
        from storage import text
        name=text(name,80,'项目名称',True)
        if any(c in name for c in ',，、\n\r'):raise ValueError('项目名称不能包含逗号、顿号或换行。')
        with self.lock,self.connect() as c:
            current=self._collection_meta(c)
            if any(p['name']==name for p in current):return {'name':name}
            p=validate_tree(current+[{'name':name,'parent':parent,'autoTags':[] if auto_tags is None else auto_tags}])[-1]
            c.execute('INSERT INTO collections(name,parent,auto_tags) VALUES(?,?,?)',(p['name'],p['parent'],json.dumps(p['autoTags'],ensure_ascii=False)));self.dirty=True
        return {'name':name}
    def update_collection(self,body):
        from storage import text,names,dump,now
        original=text(body.get('original',''),80,'原项目名称',True)
        name=text(body.get('name',original),80,'项目名称',True)
        if any(ch in name for ch in ',，、\n\r'):raise ValueError('项目名称不能包含逗号、顿号或换行。')
        with self.lock,self.connect() as c:
            current=self._collection_meta(c);old=next((p for p in current if p['name']==original),None)
            if not old:raise ValueError('项目不存在，请刷新后重试。')
            if name!=original and any(p['name']==name for p in current):raise sqlite3.IntegrityError('名称已存在')
            values={**old,**{k:body[k] for k in ('parent','autoTags','archived') if k in body},'name':name}
            proposed=[values if p['name']==original else {**p,'parent':name if p['parent']==original else p['parent']} for p in current]
            proposed=validate_tree(proposed);values=next(p for p in proposed if p['name']==name)
            apply=body.get('applyExisting',False)
            if not isinstance(apply,bool):raise ValueError('应用范围无效。')
            c.execute('UPDATE collections SET name=?,parent=?,auto_tags=?,archived=? WHERE name=?',(name,values['parent'],dump(values['autoTags']),int(values['archived']),original))
            c.execute('UPDATE collections SET parent=? WHERE parent=?',(name,original))
            # Rename all references, including trash and saved filters, in one transaction.
            for row in c.execute('SELECT * FROM resources').fetchall():
                item=self._read(c,row);changed=name!=original and (original in item['projects'] or original in item['projectNotes'])
                if changed:
                    if original in item['projectNotes'] and name in item['projectNotes'] and item['projectNotes'][original]!=item['projectNotes'][name]:raise ValueError('新名称与保留的项目备注冲突，请使用其他名称。')
                    item['projects']=[name if p==original else p for p in item['projects']]
                    item['projectNotes']={name if p==original else p:note for p,note in item['projectNotes'].items()}
                    item['collection']=item['projects'][0] if item['projects'] else '';self._projects(c,item)
                if apply and not row['deleted']:
                    parents={p['name']:p['parent'] for p in proposed};branch=set()
                    for p in proposed:
                        n=p['name']
                        while n:
                            if n==name:branch.add(p['name']);break
                            n=parents[n]
                    memberships=[p for p in item['projects'] if p in branch]
                    if memberships:
                        self._apply_auto_tags(c,item,{'projects':[p for p in item['projects'] if p not in memberships]});changed=True
                if changed:
                    item['updatedAt']=now();c.execute('UPDATE resources SET payload=? WHERE id=?',(dump({k:v for k,v in item.items() if k not in ('deleted','attachments')}),item['id']))
            if name!=original:
                for row in c.execute('SELECT * FROM smart_collections').fetchall():
                    filters=json.loads(row['filters'])
                    if filters.get('collection')==original:filters['collection']=name;c.execute('UPDATE smart_collections SET filters=? WHERE id=?',(dump(filters),row['id']))
            self.dirty=True
        return {'name':name,'parent':values['parent'],'archived':values['archived']}

    def assign_projects(self,body,*,selection_revision=None,id_limit=10000):
        from storage import names,identifier
        if not isinstance(body,dict) or set(body)!={'ids','projects'}:raise ValueError('项目归属选项无效。')
        ids=[identifier(i) for i in names(body['ids'],id_limit)]
        projects=names(body['projects'],30)
        if not ids or not projects:raise ValueError('请选择资源和项目。')
        with self.lock,self.connect() as c:
            c.execute('BEGIN IMMEDIATE');self.check_query_revision(c,selection_revision)
            meta={p['name']:p for p in self._collection_meta(c)}
            for name in projects:
                if name not in meta:raise ValueError('项目已变化，请重新打开项目选择器。')
                ancestor=name
                while ancestor:
                    if meta[ancestor]['archived']:raise ValueError('项目或上级已归档，请重新选择。')
                    ancestor=meta[ancestor]['parent']
            items=self._get_many(c,ids,True);changed=0
            for item in items:
                combined=list(dict.fromkeys(item['projects']+projects))
                if combined==item['projects']:continue
                names(combined,30)
                existing=dict(item);item['projects']=combined
                self._write(c,item,existing);changed+=1
            return {'changed':changed,'resources':len(items),'projects':projects}

    def remove_projects(self,body,*,selection_revision=None,id_limit=10000):
        from storage import names,identifier
        if not isinstance(body,dict) or set(body)!={'ids','projects'}:raise ValueError('项目归属选项无效。')
        ids=[identifier(i) for i in names(body['ids'],id_limit)];projects=names(body['projects'],30)
        if not ids or not projects:raise ValueError('请选择资源和项目。')
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE');self.check_query_revision(c,selection_revision)
                    known={p['name'] for p in self._collection_meta(c)}
                    if any(p not in known for p in projects):raise ValueError('项目已变化，请重新打开项目选择器。')
                    items=self._get_many(c,ids,True);changed=0
                    for item in items:
                        remaining=[p for p in item['projects'] if p not in projects]
                        if remaining==item['projects']:continue
                        self._write(c,{'projects':remaining},item,apply_auto=False);changed+=1
                    return {'changed':changed,'resources':len(items),'projects':projects}
            except Exception:
                self.dirty=previous_dirty
                raise
