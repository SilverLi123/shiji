"""Optional metadata after persistence. No schema, network worker or cover policy changes."""
import threading
from urllib.parse import urlsplit
SLOTS=threading.BoundedSemaphore(4)
def fallback_title(url):
    from storage import normalize_url
    p=urlsplit(normalize_url(url));parts=[x for x in p.path.split('/') if x]
    if p.hostname.lower() in ('github.com','www.github.com') and len(parts)>=2:return ('/'.join(parts[:2])+' · GitHub')[:200]
    return p.hostname[:200]
class QuickCaptureOperations:
    def enrich_capture(self,rid,body):
        from storage import identifier,normalize_url,text
        rid=identifier(rid)
        if not isinstance(body,dict) or set(body)!={'url','updatedAt'}:raise ValueError('网页补全选项无效。')
        url=normalize_url(body['url']);revision=text(body['updatedAt'],40,'资源版本',True)
        def matches(item):return not item['deleted'] and item['kind']=='website' and item['url']==url and item['updatedAt']==revision
        original=self.get(rid)
        if not matches(original) or original['title']!=fallback_title(url) or original['description']:
            return {'status':'skipped','resource':original}
        if not SLOTS.acquire(False):return {'status':'unavailable','resource':original}
        try:
            from capture import metadata
            try:result=metadata(url)
            except (OSError,ValueError):return {'status':'unavailable','resource':self.get(rid)}
            if result.get('status')!='ok':return {'status':'unavailable','resource':self.get(rid)}
            # Network I/O is outside the global lock. The final revision check and
            # changed-field write are atomic; ANY intervening edit wins.
            with self.lock:
                current=self.get(rid)
                if not matches(current) or current['attachments']!=original['attachments'] or current['coverId']!=original['coverId']:
                    return {'status':'skipped','resource':current}
                changes={key:result[key] for key in ('title','description') if isinstance(result.get(key),str) and result[key].strip() and result[key]!=current[key]}
                if not changes:return {'status':'unavailable','resource':current}
                updated=self.edit_resource(rid,{'changes':changes,'expected':{k:current[k] for k in changes}})
                return {'status':'completed','resource':updated['resource']}
        finally:SLOTS.release()
