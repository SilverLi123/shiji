"""Atomic changed-field editing without overwriting unrelated newer data."""

FIELDS=frozenset(('url','title','kind','category','description','notes','snippet','language','author','sourceUrl','parentId','price','license','thumbnail','licenseUrl','favicon','tags','projects','projectNotes','favorite','inbox','coverId'))

class EditConflict(ValueError):
    def __init__(self,resource,conflicts):
        self.resource=resource;self.conflicts=conflicts
        super().__init__('部分内容已在其他页面修改，请比较最新内容后再保存。')

class GuardedEditOperations:
    def edit_resource(self,rid,body):
        from storage import identifier,validate,text
        rid=identifier(rid)
        if not isinstance(body,dict) or set(body)!={'changes','expected'}:raise ValueError('编辑选项无效。')
        changes=body['changes'];expected=body['expected']
        if not isinstance(changes,dict) or not isinstance(expected,dict) or set(changes)!=set(expected) or not set(changes)<=FIELDS:raise ValueError('编辑字段或原值无效。')
        if 'projectNotes' in changes:
            a=changes['projectNotes'];b=expected['projectNotes']
            if not isinstance(a,dict) or not isinstance(b,dict) or set(a)!=set(b) or len(a)>1000:raise ValueError('项目备注选项无效。')
            for key,value in a.items():
                if text(key,80,'项目名称',True)!=key:raise ValueError('项目名称无效。')
                text(value,2000,'项目备注')
                if b[key] is not None:text(b[key],2000,'备注原值')
        with self.lock:
            previous_dirty=self.dirty
            try:
                with self.connect() as c:
                    current=self._get(c,rid,True)
                    # Validate the supplied baseline's types and bounds without normalizing
                    # its values for comparison (stored exact strings remain the baseline).
                    neutral={**current,'kind':'file','url':'https://example.invalid/','projects':[],'projectNotes':{}}
                    for field,value in expected.items():
                        if field!='projectNotes':validate({field:value},neutral)
                    desired=dict(current)
                    for field,value in changes.items():desired[field]=validate({field:value},neutral)[field]
                    conflicts=[]
                    for field in changes:
                        if field=='projectNotes':
                            for key in changes[field]:
                                old=current[field].get(key);value=desired[field][key]
                                if old!=value and old!=expected[field][key]:conflicts.append({'field':field,'key':key,'current':old,'value':value})
                        elif current[field]!=desired[field] and current[field]!=expected[field]:conflicts.append({'field':field,'current':current[field],'value':desired[field]})
                    if conflicts:raise EditConflict(current,conflicts)
                    # Only a matching baseline may proceed to whole-record validation.
                    desired=validate(changes,current)
                    if 'coverId' in changes and current['coverId']!=desired['coverId'] and desired['coverId']:
                        row=c.execute('SELECT resource_id,payload,deleted FROM attachments WHERE id=?',(desired['coverId'],)).fetchone()
                        if not row or row['resource_id']!=rid or row['deleted']:raise ValueError('封面图片不存在。')
                        import json
                        cover=json.loads(row['payload'])
                        if not cover['mime'].startswith('image/'):raise ValueError('封面需要图片附件。')
                        desired['colors']=cover['colors']
                    different=any(current[k]!=desired[k] for k in FIELDS) or current['colors']!=desired['colors']
                    if not different:return {'resource':current,'changed':False}
                    self._write(c,desired,current)
                    return {'resource':self._get(c,rid,True),'changed':True}
            except Exception:
                self.dirty=previous_dirty
                raise

    def cache_cover(self,rid,raw,source_url,expected_thumbnail):
        """Automatic fetched covers never replace a newer user cover or thumbnail."""
        with self.lock:
            with self.connect() as c:current=self._get(c,rid,True)
            if current['coverId'] or current['thumbnail']!=expected_thumbnail:
                return {'resource':current,'skipped':True}
            return self.attachment(rid,raw,{'name':'网页封面','cover':True,'sourceUrl':source_url})
