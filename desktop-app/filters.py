"""Extra saved-search constraints; validation is shared by preview and storage."""
import re
import unicodedata
from datetime import date

def advanced_filters(raw,result):
    from storage import text,names
    result['tagMode']=raw.get('tagMode','all')
    if result['tagMode'] not in ('all','any'):raise ValueError('请选择匹配全部标签或任一标签。')
    result['excludeTags']=names(raw.get('excludeTags',[]),30,50)
    domain=text(raw.get('domain',''),253,'网站域名').lower().rstrip('.')
    if domain:
        original=unicodedata.normalize('NFC',domain)
        try:
            domain=original.encode('idna').decode('ascii')
            # stdlib IDNA 2003 can silently replace ß/final sigma or remove
            # joiners. Browser URL hosts use newer mappings. Refuse changes to
            # Unicode identity rather than matching an unrelated ASCII host.
            if not original.isascii() and domain.encode('ascii').decode('idna')!=original:
                raise ValueError('这个国际域名的字符转换会改变名称。请填写浏览器地址栏中的 ASCII 域名（xn--…），再重新预览。')
        except UnicodeError:raise ValueError('请输入有效的网站域名，例如 reactbits.dev。')
        if len(domain)>253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',part) for part in domain.split('.')):raise ValueError('域名只填写主机名称，例如 reactbits.dev；不要包含协议、路径或端口。')
    result['domain']=domain
    for key in ('includeSubdomains','noTags','noProjects','hasNotes'):
        value=raw.get(key,key=='includeSubdomains')
        if not isinstance(value,bool):raise ValueError('筛选条件无效。')
        result[key]=value
    result['mediaType']=raw.get('mediaType','')
    if result['mediaType'] not in ('','image','audio','video','other'):raise ValueError('附件类型无效。')
    for key in ('createdFrom','createdTo'):
        value=text(raw.get(key,''),10,'收藏日期')
        if value:
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError()
                date.fromisoformat(value)
            except ValueError:raise ValueError('收藏日期需为有效的 YYYY-MM-DD 日期。')
        result[key]=value
    if result['createdFrom'] and result['createdTo'] and result['createdFrom']>result['createdTo']:raise ValueError('开始日期不能晚于结束日期。')
    return result
