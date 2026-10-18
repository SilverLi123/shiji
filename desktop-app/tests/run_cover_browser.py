"""Actual Cover Studio + existing API, isolated Store and ephemeral local port."""
import argparse,json,subprocess,sys,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage import Store
from test_cover_preferences import image_bytes

SAMPLES=[
 ('SHIJI','https://github.com/SilverLi123/shiji','website','开发工具',['GitHub'],'Python · Swift'),
 ('React','https://github.com/facebook/react','website','开发工具',['React','组件'],'JavaScript'),
 ('React Bits','https://reactbits.dev/','website','UI / 设计',['React','组件'],'JavaScript'),
 ('Recent — Design Inspiration','https://www.recent.co/','website','灵感',['设计','灵感'],''),
 ('Motion Sites','https://motionsites.ai/','website','视频',['动效'],''),
 ('Poly Haven','https://polyhaven.com/','website','3D',['3D','素材'],''),
 ('Hugging Face','https://huggingface.co/models','website','开发工具',['AI','模型'],''),
 ('ROS 2 Robotics','https://docs.ros.org/en/rolling/','website','开发工具',['机器人'],''),
 ('Freesound','https://freesound.org/','website','音频',['音频'],''),
 ('中文技术文章：在本地优先的工具中保持资源索引、封面和附件引用一致','https://example.test/article','website','其他',['中文','文章'],''),
 ('保留原始空格的 JavaScript 代码片段','','code','开发工具',['代码'],'JavaScript'),
 ('中英文 Prompt — 用具体约束组织真实设计参考','','prompt','灵感',['Prompt'],''),
 ('真实本地图片 · 隔离验收素材','','file','美术素材',['图片'],''),
]
def run():
 parser=argparse.ArgumentParser();parser.add_argument('--count',type=int,default=1000);parser.add_argument('--out',default='dist/v64-cover-browser');args=parser.parse_args()
 with tempfile.TemporaryDirectory(prefix='shiji-v64-cover-') as directory:
  store=Store(directory);ids=[]
  with store.lock,store.connect() as c:
   for i in range(max(0,args.count-len(SAMPLES))):store._write(c,{'kind':'code','title':'隔离性能样本 '+str(i),'snippet':'const value = '+str(i),'category':'开发工具'})
   for i,(title,url,kind,category,tags,language) in enumerate(SAMPLES):
    r=store._write(c,{'title':title,'url':url,'kind':kind,'category':category,'tags':tags,'language':language,'notes':'隔离 UI 验收样本，不是用户收藏。','snippet':'const result = items.filter(item => item.enabled);\n  return result;' if kind=='code' else '请根据真实资源信息整理设计参考，不虚构来源与技术参数。' if kind=='prompt' else '', 'coverConfig':{'imageSource':'poster'}});ids.append(r['id'])
  store.attachment(ids[-1],image_bytes(),{'name':'QA actual.png','cover':True})
  store.save({'coverConfig':None},ids[-1]);image=Path(directory)/'upload.png';image.write_bytes(image_bytes())
  class Handler(server.Handler):
   def log_message(self,*args):pass
  old=server.STORE;server.STORE=store;http=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
  try:
   out=Path(__file__).resolve().parents[1]/args.out;out.mkdir(parents=True,exist_ok=True)
   subprocess.run(['node',str(Path(__file__).with_name('cover_browser.cjs')),f'http://127.0.0.1:{http.server_port}/',str(out),json.dumps(ids),str(image)],check=True,timeout=240)
  finally:http.shutdown();http.server_close();worker.join();store.stop_search_worker();server.STORE=old
if __name__=='__main__':run()
