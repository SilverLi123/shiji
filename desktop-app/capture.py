"""Bounded public-web requests, pinned DNS addresses and HTML metadata."""
import http.client
import ipaddress
import re
import socket
import ssl
import time
import queue
import threading
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from storage import normalize_url

def resolve_public(url):
    url=normalize_url(url);parts=urlsplit(url);host=parts.hostname.encode('idna').decode();port=parts.port or (443 if parts.scheme=='https' else 80)
    if port not in (80,443) or host.lower() in ('localhost',) or host.lower().endswith(('.localhost','.local')):raise ValueError('只支持公开网站的标准 HTTP / HTTPS 地址。')
    addresses={r[4][0] for r in socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(x).is_global for x in addresses):raise ValueError('不能读取本机或内网网址。')
    return url,host,port,sorted(addresses)[0]
def _request(target,method,limit,timeout):
    url,host,port,address=target;p=urlsplit(url);connection=http.client.HTTPConnection(host,port,timeout=timeout);deadline=time.monotonic()+timeout
    sock=socket.socket(socket.AF_INET6 if ':' in address else socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(timeout)
    def abort():
        try:sock.shutdown(socket.SHUT_RDWR)
        except OSError:pass
        sock.close()
    timer=threading.Timer(timeout,abort);timer.daemon=True;timer.start()
    try:
        sock.connect((address,port))
        if p.scheme=='https':
            sock=ssl.create_default_context().wrap_socket(sock,server_hostname=host,do_handshake_on_connect=False)
            sock.do_handshake()
        connection.sock=sock
        path=p.path or '/'
        if p.query:path+='?'+p.query
        connection.request(method,path,headers={'User-Agent':'ShijiResourceLibrary/0.4 (+local bookmark manager)','Accept':'text/html,application/xhtml+xml,image/*,*/*;q=0.5','Accept-Encoding':'identity','Connection':'close'})
        response=connection.getresponse();headers={k.lower():v for k,v in response.getheaders()};data=response.read(limit+1) if method!='HEAD' and response.status not in (301,302,303,307,308) else b''
        if time.monotonic()>=deadline:raise TimeoutError('读取超时。')
        if len(data)>limit:raise ValueError('网页或图片超过读取大小限制。')
        return response.status,headers,data
    finally:timer.cancel();connection.close();sock.close()
def bounded_resolve(url,timeout):
    # getaddrinfo cannot be interrupted portably; return on deadline and leave
    # only a daemon DNS worker. Bound their count so repeated failures cannot grow threads.
    if not DNS_SLOTS.acquire(blocking=False):raise TimeoutError('DNS 查询繁忙，请稍后重试。')
    result=queue.Queue(maxsize=1)
    def worker():
        try:result.put((True,resolve_public(url)))
        except Exception as e:result.put((False,e))
        finally:DNS_SLOTS.release()
    threading.Thread(target=worker,daemon=True).start()
    try:ok,value=result.get(timeout=max(.001,timeout))
    except queue.Empty:raise TimeoutError('DNS 查询超时。')
    if not ok:raise value
    return value
DNS_SLOTS=threading.BoundedSemaphore(8)
def public_fetch(url,method='GET',limit=2*1024*1024,timeout=8):
    deadline=time.monotonic()+timeout
    for _ in range(5):
        target=bounded_resolve(url,deadline-time.monotonic());remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('读取超时。')
        status,headers,data=_request(target,method,limit,remaining)
        if status in (301,302,303,307,308):
            location=headers.get('location')
            if not location:raise ValueError('重定向没有目标地址。')
            url=urljoin(target[0],location);continue
        return status,headers,data,target[0]
    raise ValueError('网页重定向次数过多。')
class MetaParser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.title_parts=[];self.in_title=False;self.meta={};self.icon='';self.canonical=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='meta' and a.get('content'):self.meta[(a.get('property') or a.get('name') or '').lower()]=a['content']
        if tag=='link' and 'icon' in a.get('rel','').lower().split() and a.get('href'):self.icon=a['href']
        if tag=='link' and 'canonical' in a.get('rel','').lower().split() and a.get('href'):self.canonical=a['href']
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title_parts.append(data)
def safe_asset(base,value):
    if not value:return ''
    try:
        url=normalize_url(urljoin(base,value));host=urlsplit(url).hostname
        if host=='localhost' or host.endswith(('.local','.localhost')):return ''
        try:
            if not ipaddress.ip_address(host).is_global:return ''
        except ValueError:pass
        return url
    except ValueError:return ''
def metadata_from_html(url,raw,charset='utf-8'):
    try:html=raw.decode(charset,errors='replace')
    except LookupError:html=raw.decode('utf-8',errors='replace')
    parser=MetaParser();parser.feed(html)
    clean=lambda v,n:re.sub(r'\s+',' ',v).strip()[:n]
    return {'url':url,'title':clean(parser.meta.get('og:title') or parser.meta.get('twitter:title') or ''.join(parser.title_parts),200),'description':clean(parser.meta.get('og:description') or parser.meta.get('description') or parser.meta.get('twitter:description') or '',1000),'thumbnail':safe_asset(url,parser.meta.get('og:image') or parser.meta.get('twitter:image') or ''),'favicon':safe_asset(url,parser.icon or '/favicon.ico'),'canonicalUrl':safe_asset(url,parser.canonical),'sourceHost':urlsplit(url).hostname}
def metadata(url):
    try:
        status,headers,raw,final=public_fetch(url)
        if status>=400:return {'status':'unknown','message':'网站暂不允许读取，可手动填写。','url':normalize_url(url)}
        if 'html' not in headers.get('content-type',''):return {'status':'unknown','message':'这不是 HTML 页面，可手动填写。','url':final}
        match=re.search(r'charset=([\w-]+)',headers.get('content-type',''))
        result=metadata_from_html(final,raw,match.group(1) if match else 'utf-8');result['status']='ok';result['message']='已读取网页信息。' if result['title'] else '网页没有提供标题，可手动填写。';return result
    except (OSError,ValueError,http.client.HTTPException):return {'status':'unknown','message':'未能读取网页信息，可以直接手动保存。'}

def capture_image(url):
    """A URL becomes a local image only after a bounded, validated download."""
    from capture_images import validate_image
    from capture_jobs import CaptureFailure
    status,headers,raw,final=public_fetch(url,limit=5*1024*1024)
    if status!=200:raise CaptureFailure('image-http','真实图片暂时无法读取。',status>=500 or status in (408,429))
    try:validate_image(raw,headers.get('content-type',''))
    except ValueError as e:raise CaptureFailure('image-invalid','图片类型、尺寸或文件校验失败。',False) from e
    return raw,final,'og:image'

def capture_payload(url,cover_url='',need_cover=True):
    """Fetch one page, then an optional real image; never changes the saved URL."""
    from capture_jobs import CaptureFailure
    try:
        status,headers,raw,final=public_fetch(url)
        if status>=400:raise CaptureFailure('http','网站限制读取或暂时不可用，原收藏已保留。',status>=500 or status in (408,429))
        if 'html' not in headers.get('content-type','').lower():return {'metadata':{},'image':None}
        match=re.search(r'charset=([\w-]+)',headers.get('content-type',''),re.I)
        meta=metadata_from_html(final,raw,match.group(1) if match else 'utf-8')
        meta['sourceUrl']=final
        result={'metadata':meta,'image':None}
        target=cover_url or meta['thumbnail']
        if need_cover and target:
            try:result['image']=capture_image(target)
            except CaptureFailure as e:result['coverError']={'code':e.code,'retryable':e.retryable}
            except (OSError,ValueError,http.client.HTTPException):result['coverError']={'code':'image-network','retryable':True}
        return result
    except CaptureFailure:raise
    except socket.gaierror as e:raise CaptureFailure('dns','DNS 查询失败，原收藏已保留。') from e
    except TimeoutError as e:raise CaptureFailure('timeout','读取超时，原收藏已保留。') from e
    except ValueError as e:raise CaptureFailure('blocked','地址或响应未通过公网安全校验。',False) from e
    except (OSError,http.client.HTTPException) as e:raise CaptureFailure('network','连接暂时失败，原收藏已保留。') from e
def classify_status(code):
    return 'ok' if 200<=code<400 else 'broken' if code in (404,410) else 'unknown'
def check_link(url):
    try:
        status,_,_,_=public_fetch(url,'HEAD',limit=1024)
        if status==405:status,_,_,_=public_fetch(url,'GET',limit=2*1024*1024)
        result=classify_status(status)
        return {'status':result,'message':{'ok':'网站可访问','broken':'页面返回 '+str(status),'unknown':'访问受限或暂时无法判断（'+str(status)+'）'}[result]}
    except (OSError,ValueError,http.client.HTTPException):return {'status':'unknown','message':'连接失败或检查超时，可以稍后重试。'}

# Headless Chrome uses an isolated profile and a public-only explicit proxy.
# Chromium docs: net/docs/proxy.md (<-loopback> disables implicit bypass).
def chrome_binary():
    import shutil
    from pathlib import Path
    mac=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    return str(mac) if mac.is_file() else shutil.which('google-chrome') or shutil.which('chromium')

def chrome_screenshot(url,timeout=20):
    import os
    import select
    import signal
    import subprocess
    import tempfile
    from pathlib import Path
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    target=bounded_resolve(url,8);binary=chrome_binary()
    if not binary:raise ValueError('未找到本机 Chrome，可手动上传截图。')
    class PublicProxy(ThreadingHTTPServer):
        daemon_threads=True
        def __init__(self):
            super().__init__(('127.0.0.1',0),Proxy);self.slots=threading.BoundedSemaphore(16);self.guard=threading.Lock();self.total=0;self.requests=0;self.received=0
        def process_request(self,request,address):
            with self.guard:self.requests+=1;allowed=self.requests<=256
            if not allowed or not self.slots.acquire(False):self.shutdown_request(request);return
            try:super().process_request(request,address)
            except Exception:self.slots.release();raise
        def process_request_thread(self,request,address):
            try:super().process_request_thread(request,address)
            finally:self.slots.release()
        def budget(self,count):
            with self.guard:
                self.total+=count
                if self.total>128*1024*1024:raise ValueError('截图页面超过读取限制。')
    class Proxy(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def setup(self):super().setup();self.connection.settimeout(5)
        def do_CONNECT(self):
            remote=None
            try:
                # All redirect and subresource CONNECTs resolve/pin afresh.
                checked=bounded_resolve('https://'+self.path+'/',5)
                remote=socket.create_connection((checked[3],checked[2]),timeout=5)
                self.send_response(200);self.end_headers();self.wfile.flush()
                deadline=time.monotonic()+timeout;received=0
                while time.monotonic()<deadline:
                    ready,_,_=select.select([self.connection,remote],[],[],.25)
                    for incoming in ready:
                        data=incoming.recv(65536)
                        if not data:return
                        self.server.budget(len(data));received+=len(data)
                        if received>32*1024*1024:return
                        (remote if incoming is self.connection else self.connection).sendall(data)
                        if incoming is remote:
                            with self.server.guard:self.server.received+=len(data)
            except (ValueError,OSError,http.client.HTTPException):
                if remote is None:self.send_error(403,'Public HTTP/HTTPS only')
            finally:
                if remote:remote.close()
                self.close_connection=True
        def do_GET(self):
            try:
                status,headers,data,_=public_fetch(self.path,limit=5*1024*1024,timeout=8);self.server.budget(len(data))
                self.send_response(status);self.send_header('Content-Type',headers.get('content-type','application/octet-stream'));self.send_header('Content-Length',str(len(data)));self.send_header('Connection','close');self.end_headers();self.wfile.write(data)
                with self.server.guard:self.server.received+=len(data)
            except (ValueError,OSError,http.client.HTTPException):self.send_error(403,'Public HTTP/HTTPS only')
            self.close_connection=True
        def do_POST(self):self.send_error(405)
    proxy=PublicProxy();worker=threading.Thread(target=proxy.serve_forever,daemon=True);worker.start()
    try:
        with tempfile.TemporaryDirectory(prefix='shiji-chrome-') as directory:
            output=Path(directory)/'preview.png'
            args=[binary,'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-background-networking','--disable-sync','--disable-quic','--force-webrtc-ip-handling-policy=disable_non_proxied_udp','--host-resolver-rules=MAP * ~NOTFOUND','--proxy-server=http://127.0.0.1:'+str(proxy.server_port),'--proxy-bypass-list=<-loopback>','--user-data-dir='+str(Path(directory)/'profile'),'--window-size=1280,800','--hide-scrollbars','--timeout=12000','--screenshot='+str(output),target[0]]
            process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            try:
                process.wait(timeout=timeout)
                if process.returncode or not output.is_file() or output.stat().st_size>5*1024*1024 or proxy.received<1024:raise ValueError('Chrome 未能生成可用截图。')
                raw=output.read_bytes()
                if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Chrome 截图格式不正确。')
                return raw,target[0]
            except subprocess.TimeoutExpired as e:raise TimeoutError('Chrome 截图超时。') from e
            finally:
                # Kill the whole isolated process group, including renderers.
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
    finally:proxy.shutdown();proxy.server_close();worker.join(timeout=2)

def website_preview(url):
    from storage import detect_mime
    # Reject private addresses even when metadata fails and falls back to Chrome.
    bounded_resolve(url,8)
    try:
        status,headers,raw,final=public_fetch(url)
        if status==200 and 'html' in headers.get('content-type',''):
            match=re.search(r'charset=([\w-]+)',headers.get('content-type',''));meta=metadata_from_html(final,raw,match.group(1) if match else 'utf-8')
            if meta['thumbnail']:
                status,_,image,image_url=public_fetch(meta['thumbnail'],limit=5*1024*1024)
                if status==200 and detect_mime(image).startswith('image/'):return image,image_url,'og:image'
    except (ValueError,OSError,http.client.HTTPException):pass
    raw,final=chrome_screenshot(url);return raw,final,'Chrome 截图'
