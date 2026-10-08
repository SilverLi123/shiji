#!/usr/bin/env python3
"""Local-only resource workbench, Python standard library."""
import base64
import tempfile
from contextlib import contextmanager
from backups import CHUNK,MAX_ARCHIVE
import hmac
from concurrent.futures import ThreadPoolExecutor
from capture import metadata as read_metadata, check_link, public_fetch, safe_asset
from storage import normalize_url, detect_mime, text,NoteConflict,EditConflict
import argparse
import json
import re
import sqlite3
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from storage import Store, Duplicate
ROOT=Path(__file__).resolve().parent
STORE=None
DEMO = [
    ('MDN Web Docs', 'https://developer.mozilla.org/', '开发工具', ['文档', 'Web'], '查阅 Web API 和前端开发文档。'),
    ('Figma Community', 'https://www.figma.com/community', 'UI / 设计', ['UI', '组件'], '寻找社区设计文件与界面参考。'),
    ('Unsplash', 'https://unsplash.com/', '美术素材', ['摄影', '图片'], '保存图片来源；使用前确认具体授权。'),
    ('Google Fonts', 'https://fonts.google.com/', '字体', ['字体', '排版'], '为项目寻找字体并记录许可。'),
    ('Freesound', 'https://freesound.org/', '音频', ['音效', '游戏'], '寻找音效；不同文件的许可可能不同。'),
    ('Mixkit', 'https://mixkit.co/', '视频', ['视频', '素材'], '查看素材资源，下载前确认具体使用条件。'),
    ('Awwwards', 'https://www.awwwards.com/', '灵感', ['网页', '交互'], '收集网页设计和交互灵感。'),
    ('Poly Haven', 'https://polyhaven.com/', '3D', ['3D', '材质'], '记录 3D 素材来源和项目用途。'),
]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'static'),**kwargs)
    def end_headers(self):
        if urlsplit(self.path).path in {'/api/clip','/api/clip/ping'} and re.fullmatch(r'chrome-extension://[a-z]{32}',self.headers.get('Origin','')):self.send_header('Access-Control-Allow-Origin',self.headers['Origin'])
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');super().end_headers()
    def send_json(self,status,payload,attachment=False):
        raw=json.dumps(payload,ensure_ascii=False).encode();self.send_bytes(status,raw,'application/json; charset=utf-8','shiji-bookmarks.json' if attachment else None)
    def send_bytes(self,status,raw,mime,filename=None):
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
        if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
        self.end_headers();self.wfile.write(raw)
    def safe_request(self):
        allowed={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
        clip=urlsplit(self.path).path in {'/api/clip','/api/clip/ping'}
        origin=self.headers.get('Origin','')
        extension_origin=not origin or bool(re.fullmatch(r'chrome-extension://[a-z]{32}',origin))
        paired=clip and extension_origin and hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+STORE.token())
        if self.headers.get('Host','') not in allowed or (clip and not paired) or (not paired and origin and origin not in {'http://'+x for x in allowed}):
            self.send_json(403,{'error':'只能从本机资源库页面访问。'});return False
        return True
    def read_json(self):
        if not self.headers.get('Content-Type','').startswith('application/json'):raise ValueError('请使用 JSON 格式提交。')
        return json.loads(self.read_bytes(12*1024*1024))
    def read_bytes(self,limit):
        size=int(self.headers.get('Content-Length','0'))
        if size<=0 or size>limit:raise ValueError('文件为空或超过大小限制。')
        raw=self.rfile.read(size)
        if len(raw)!=size:raise ValueError('文件没有上传完整，请重试。')
        return raw
    def do_GET(self):
        if not self.safe_request():return
        try:
            path=urlsplit(self.path).path
            if path=='/api/resources':self.send_json(200,STORE.state())
            elif re.fullmatch(r'/api/resources/[^/]+',path):self.send_json(200,{'resource':STORE.get(path.split('/')[-1])})
            elif path=='/api/pairing':self.send_json(200,{'token':STORE.token()})
            elif path=='/api/backup.zip':
                with STORE.backup_path() as archive:self.send_disk(archive,'application/zip','shiji-full-backup.zip')
            elif path=='/api/backups':self.send_json(200,STORE.backup_list())
            elif path=='/api/website-previews':self.send_json(200,STORE.preview_status())
            elif path=='/api/library-health':self.send_json(200,STORE.health_status())
            elif path=='/api/library-health/report':
                report=STORE.health_status()['report']
                if not report:raise ValueError('先完成一次附件检查，再下载报告。')
                self.send_bytes(200,json.dumps(report,ensure_ascii=False,indent=2).encode(),'application/json; charset=utf-8','shiji-attachment-health.json')
            elif path.startswith('/api/backups/'):
                file=STORE.backup_file(path.split('/')[-1]);self.send_disk(file,'application/zip',file.name)
            elif path.startswith('/api/files/'):
                item,file=STORE.file(path.split('/')[-1]);self.send_file(item,file)
            elif path=='/api/trash':self.send_json(200,STORE.state(True))
            elif path=='/api/export':self.send_json(200,STORE.export(),True)
            elif path.startswith('/api/'):self.send_json(404,{'error':'接口不存在。'})
            else:super().do_GET()
        except (BrokenPipeError,ConnectionResetError,ConnectionError):return
        except (ValueError,KeyError) as e:self.send_json(400,{'error':str(e)})
        except (OSError,sqlite3.Error):self.send_json(500,{'error':'备份或文件读取失败，请检查磁盘空间并重试。'})
    def send_disk(self,path,mime,name,media=False):
        if path.is_symlink() or not path.is_file():raise ValueError('文件缺失或无法安全读取，请用有效备份恢复。')
        with path.open('rb') as source:
            length=path.stat().st_size;start=0;end=length-1;status=200
            byte_range=self.headers.get('Range') if media else None
            if byte_range:
                match=re.fullmatch(r'bytes=(\d*)-(\d*)',byte_range)
                if not match or not any(match.groups()):
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{length}');self.send_header('Content-Length','0');self.end_headers();return
                left,right=match.groups()
                if left:start=int(left);end=min(int(right) if right else end,end)
                else:start=max(0,length-int(right))
                if start>end or start>=length:
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{length}');self.send_header('Content-Length','0');self.end_headers();return
                status=206
            self.send_response(status);self.send_header('Content-Type',mime)
            if media:self.send_header('Accept-Ranges','bytes')
            if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{length}')
            from urllib.parse import quote
            disposition='inline' if media and mime.startswith(('image/','audio/','video/')) and 'download=' not in self.path else 'attachment'
            self.send_header('Content-Disposition',disposition+"; filename*=UTF-8''"+quote(name))
            remaining=end-start+1;self.send_header('Content-Length',str(remaining));self.end_headers();source.seek(start)
            while remaining:
                block=source.read(min(CHUNK,remaining))
                if not block:raise ConnectionError('文件在下载过程中发生变化。')
                self.wfile.write(block);remaining-=len(block)
    def send_file(self,item,path):self.send_disk(path,item['mime'],item['name'],True)
    @contextmanager
    def read_archive(self):
        size=int(self.headers.get('Content-Length','0'))
        if size<=0 or size>MAX_ARCHIVE:raise ValueError('完整备份为空或超过 16 GB。')
        with tempfile.TemporaryDirectory(dir=str(STORE.root),prefix='upload-') as directory:
            path=Path(directory)/'backup.zip';remaining=size
            with path.open('wb') as target:
                while remaining:
                    block=self.rfile.read(min(CHUNK,remaining))
                    if not block:raise ValueError('备份没有上传完整，请重新选择后重试。')
                    target.write(block);remaining-=len(block)
            yield path
    def do_OPTIONS(self):
        if urlsplit(self.path).path not in {'/api/clip','/api/clip/ping'} or not re.fullmatch(r'chrome-extension://[a-z]{32}',self.headers.get('Origin','')):self.send_json(403,{'error':'不支持跨站请求。'});return
        allowed={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
        if self.headers.get('Host') not in allowed:self.send_json(403,{'error':'本地地址不正确。'});return
        self.send_response(204);self.send_header('Access-Control-Allow-Methods','POST');self.send_header('Access-Control-Allow-Headers','Content-Type,Authorization');self.end_headers()
    def do_POST(self):self.mutate('POST')
    def do_PUT(self):self.mutate('PUT')
    def do_DELETE(self):self.mutate('DELETE')
    def mutate(self,method):
        if not self.safe_request():return
        try:
            path=urlsplit(self.path).path
            if path=='/api/clip/ping' and method=='POST':
                self.send_json(200,{'app':'DevResourceLibrary','connected':True});return
            if path in ('/api/restore','/api/restore/preflight') and method=='POST':
                with self.read_archive() as archive:result=STORE.preflight_restore(archive) if path.endswith('/preflight') else STORE.restore_zip(archive)
                self.send_json(200,result)
                return
            if re.fullmatch(r'/api/resources/[^/]+/attachments',path) and method=='POST':
                metadata=json.loads(base64.b64decode(self.headers.get('X-Metadata','e30='),validate=True))
                self.send_json(200,STORE.attachment(path.split('/')[3],self.read_bytes(64*1024*1024),metadata));return
            if path=='/api/assets/import' and method=='POST':
                metadata=json.loads(base64.b64decode(self.headers.get('X-Metadata','e30='),validate=True))
                self.send_json(200,STORE.import_asset(self.read_bytes(64*1024*1024),metadata));return
            body=self.read_json() if method!='DELETE' else {}
            if not isinstance(body,dict):raise ValueError('请求格式不正确。')
            if path=='/api/metadata' and method=='POST':result=read_metadata(body.get('url',''))
            elif path=='/api/remote-cover' and method=='POST':
                rid=body.get('id');STORE.get(rid);status,headers,data,final=public_fetch(body.get('url',''),limit=5*1024*1024)
                if status!=200 or not detect_mime(data).startswith('image/'):raise ValueError('没有读到可用图片，可以粘贴或上传截图。')
                result=STORE.cache_cover(rid,data,final,body.get('url',''))
            elif path=='/api/check-links' and method=='POST':
                ids=body.get('ids',[])
                if not isinstance(ids,list) or len(ids)>20 or not ids:raise ValueError('一次请选择 1 至 20 条资源检查。')
                items=[STORE.get(rid) for rid in ids]
                def check(item):
                    if item['deleted']:raise ValueError('不能检查回收站资源。')
                    r=check_link(item['url']) if item['url'] else {'status':'unchecked','message':'本地资源没有网址。'}
                    STORE.set_link_status(item['id'],r['status'],r['message']);return {**r,'id':item['id']}
                with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,items))
                result={'results':results}
            elif path=='/api/clip' and method=='POST':
                url=normalize_url(body.get('url',''))
                selection=text(body.get('selection',''),10000,'选中文字');screenshot=body.get('screenshot','');raw=None;image=None
                if screenshot:
                    if not isinstance(screenshot,str) or not re.fullmatch(r'data:image/(png|jpeg);base64,[A-Za-z0-9+/=]+',screenshot):raise ValueError('截图格式不正确。')
                    raw=base64.b64decode(screenshot.split(',',1)[1],validate=True)
                    if not detect_mime(raw).startswith('image/'):raise ValueError('截图不是图片。')
                if body.get('imageUrl'):
                    status,_,data,final=public_fetch(body['imageUrl'],limit=5*1024*1024)
                    if status!=200 or not detect_mime(data).startswith('image/'):raise ValueError('图片未能保存，请在资源库中手动上传。')
                    image=(data,final)
                captured=STORE.capture_page({'url':url,'title':body.get('title') or urlsplit(url).hostname,'description':body.get('description',''),'thumbnail':safe_asset(url,body.get('thumbnail','')),'favicon':safe_asset(url,body.get('favicon',''))},selection)
                item=captured['resource'];added=bool(raw or image or captured['contentAdded'])
                if raw:STORE.attachment(item['id'],raw,{'name':'网页截图.png','cover':True,'sourceUrl':url})
                if image:STORE.attachment(item['id'],image[0],{'name':'网页图片','cover':not bool(raw),'sourceUrl':image[1]})
                result={'resource':STORE.get(item['id']),'alreadySaved':captured['alreadySaved'],'contentAdded':added}
            elif path=='/api/resources' and method=='POST':result=STORE.save(body)
            elif path=='/api/projects/assign' and method=='POST':result=STORE.assign_projects(body)
            elif path=='/api/projects/remove' and method=='POST':result=STORE.remove_projects(body)
            elif path=='/api/collections' and method=='POST':result=STORE.collection(body.get('name'),body.get('parent',''),body.get('autoTags',[]))
            elif path=='/api/collections/update' and method=='POST':result=STORE.update_collection(body)
            elif path=='/api/bookmarks/preview' and method=='POST':result=STORE.preview_bookmarks(body)
            elif path=='/api/assets/preview' and method=='POST':result=STORE.preview_assets(body)
            elif path=='/api/assets/validate' and method=='POST':result=STORE.validate_asset_options(body)
            elif path=='/api/bookmarks/import' and method=='POST':result=STORE.import_bookmarks(body)
            elif path=='/api/links/preview' and method=='POST':result=STORE.preview_links(body)
            elif path=='/api/links/import' and method=='POST':result=STORE.import_links(body)
            elif path=='/api/backups' and method=='POST':result=STORE.create_backup()
            elif path=='/api/website-previews' and method=='POST':result=STORE.configure_previews(body)
            elif path=='/api/backups/preflight' and method=='POST':result=STORE.preflight_backup(body.get('name',''))
            elif path=='/api/restore/confirm' and method=='POST':result=STORE.confirm_restore(body)
            elif path=='/api/restore/cancel' and method=='POST':result=STORE.cancel_restore(body.get('ticket'))
            elif path=='/api/undo' and method=='POST':result=STORE.undo(body.get('token'))
            elif path=='/api/library-health/share' and method=='POST':result=STORE.start_sharing(body)
            elif path=='/api/library-health' and method=='POST':result=STORE.start_health(body.get('cancel',False))
            elif path.startswith('/api/attachments/') and method=='PUT':result=STORE.update_attachment(path.split('/')[-1],body)
            elif path=='/api/batch' and method=='POST':result=STORE.batch(body)
            elif path=='/api/tags/assign' and method=='POST':result=STORE.assign_tags(body)
            elif path=='/api/tags' and method=='POST':result=STORE.rename_tag(body.get('from'),body.get('to'))
            elif path=='/api/smart-collections' and method=='POST':result=STORE.smart(body)
            elif path.startswith('/api/smart-collections/') and method=='PUT':
                try:result=STORE.smart(body,path.split('/')[-1])
                except KeyError as e:return self.send_json(404,{'error':str(e)})
            elif path=='/api/filters/validate' and method=='POST':
                from storage import validate_filters
                result={'filters':validate_filters(body.get('filters',{}))}
            elif path.startswith('/api/smart-collections/') and method=='DELETE':result=STORE.delete_smart(path.split('/')[-1])
            elif path=='/api/import' and method=='POST':result=STORE.import_json(body)
            elif path=='/api/demo' and method=='POST':
                added=0;known={x['url'] for x in STORE.state()['resources']}|{x['url'] for x in STORE.state(True)['resources']}
                for title,url,category,tags,description in DEMO:
                    if url in known:continue
                    STORE.save({'title':title,'url':url,'category':category,'tags':tags,'description':description,'demo':True});added+=1
                result={'added':added}
            elif path=='/api/clear-demo' and method=='POST':
                ids=[x['id'] for x in STORE.state()['resources'] if x['demo']]
                if ids:STORE.batch({'ids':ids,'action':'delete'})
                result={'removed':len(ids),'ids':ids}
            elif path.startswith('/api/resources/'):
                parts=path.strip('/').split('/');rid=parts[2]
                if len(parts)==4 and parts[3]=='enrich' and method=='POST':result=STORE.enrich_capture(rid,body)
                elif len(parts)==4 and parts[3]=='edit' and method=='POST':result=STORE.edit_resource(rid,body)
                elif len(parts)==4 and parts[3]=='note' and method=='POST':result=STORE.update_note(rid,body)
                elif len(parts)==4 and parts[3]=='restore' and method=='POST':result=STORE.remove(rid,True)
                elif len(parts)==3 and method=='PUT':result=STORE.save(body,rid)
                elif len(parts)==3 and method=='DELETE':result=STORE.remove(rid)
                else:self.send_json(404,{'error':'资源或操作不存在。'});return
            else:self.send_json(404,{'error':'接口不存在。'});return
            self.send_json(200,result)
        except EditConflict as e:self.send_json(409,{'error':str(e),'resource':e.resource,'conflicts':e.conflicts})
        except NoteConflict as e:self.send_json(409,{'error':str(e),'current':e.current,'resource':e.resource})
        except Duplicate as e:self.send_json(409,{'error':str(e),'existingId':e.rid})
        except sqlite3.IntegrityError:self.send_json(409,{'error':'名称或网址已存在。'})
        except (ValueError,TypeError,KeyError) as e:self.send_json(400,{'error':str(e)})
        except (OSError,zipfile.BadZipFile):self.send_json(500,{'error':'文件保存失败，请检查磁盘空间或备份完整性。'})
        except sqlite3.Error:self.send_json(500,{'error':'保存失败，请检查磁盘空间或稍后重试。'})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--data-dir',type=Path,default=ROOT/'data');args=parser.parse_args()
    STORE=Store(args.data_dir);STORE.start_auto_backup();STORE.start_preview_worker();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('资源库已启动：http://127.0.0.1:{}'.format(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:STORE.stop_auto_backup();STORE.stop_preview_worker();server.server_close()
