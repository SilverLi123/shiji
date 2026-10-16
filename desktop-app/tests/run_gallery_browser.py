"""Opt-in real-browser suite, not a portable JSDOM substitute. CI installs Chromium."""
import base64,json,os,subprocess,sys,tempfile,threading,struct,zlib
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage import Store

def run():
 with tempfile.TemporaryDirectory(prefix='shiji-gallery-browser-') as root:
  store=Store(root)
  # Existing Store canonical writer, one transaction; no network or formal data.
  images=[]
  with store.lock,store.connect() as c:
   for i in range(1300):
    r={'title':('很长的中文素材名称和空间设计 ' if i%31==0 else '')+'Gallery '+str(i),'kind':'website' if i%3 else 'code','url':'https://github.com/qa/repo'+str(i),'language':'TypeScript' if i%13==0 else '', 'snippet':'const value = "Gallery";','category':'开发工具' if i%3 else 'UI / 设计','tags':['Gallery'],'notes':'QA local fixture','inbox':True}
    item=store._write(c,r)
    if i>=1290:images.append(item['id'])
  for i,rid in enumerate(images):
   w,h=[(48,32),(32,64),(64,32)][i%3]
   def chunk(kind,raw):return struct.pack('!I',len(raw))+kind+raw+struct.pack('!I',zlib.crc32(kind+raw)&0xffffffff)
   raw=b''.join(b'\0'+bytes((90,50,200))*w for _ in range(h))
   png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
   store.attachment(rid,png,{'name':'ratio QA.png','cover':True})
  class Handler(server.Handler):
   def log_message(self,*args):pass
  old=server.STORE;server.STORE=store;http=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
  try:
   output=Path(__file__).parents[1]/'dist/v63-browser-regression';output.parent.mkdir(exist_ok=True)
   subprocess.run(['node',str(Path(__file__).with_name('gallery_browser.cjs')),f'http://127.0.0.1:{http.server_port}/',str(output)],check=True,timeout=180)
  finally:http.shutdown();http.server_close();thread.join();store.stop_search_worker();server.STORE=old
if __name__=='__main__':run()
