import json,sys,tempfile,threading,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage import Store

class QueryAPI(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.old=server.STORE;server.STORE=self.store
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.http.server_port)
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();server.STORE=self.old;self.temp.cleanup()
    def request(self,path,body=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        try:
            with urlopen(Request(self.base+path,None if body is None else json.dumps(body).encode(),headers=headers)) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def test_real_capture_search_edit_backup_restore_and_legacy_paths(self):
        code,saved=self.request('/api/resources',{'url':'https://example.com/测试','title':'中文组件','quickCapture':True});self.assertEqual(code,200)
        rid=saved['resource']['id'];self.assertEqual(self.request('/api/library')[1]['queryVersion'],1)
        code,q=self.request('/api/query',{'filters':{'search':'中文'},'limit':1});self.assertEqual(code,200);self.assertEqual(q['total'],1)
        self.assertTrue(q['resources'][0]['_summary'])
        self.assertFalse(self.request('/api/resources/'+rid)[1]['resource'].get('_summary',False))
        self.assertEqual(self.request('/api/resources')[1]['resources'][0]['id'],rid)
        self.assertEqual(self.request('/api/query',{'filters':{'search':'" OR 1=1 --'}})[1]['total'],0)
        self.assertEqual(self.request('/api/query',{},'https://evil.invalid')[0],403)
        ids=self.request('/api/query/ids',{})[1]
        self.assertEqual(self.request('/api/query/batch',{'operation':'batch','revision':ids['revision'],'body':{'ids':ids['ids'],'action':'delete'}})[0],200)
        self.assertEqual(self.request('/api/query',{})[1]['total'],0)
        self.assertEqual(self.request('/api/query/batch',{'operation':'batch','revision':ids['revision'],'body':{'ids':ids['ids'],'action':'restore'}})[0],409)
    def test_invalid_query_and_cursor_returns_safe_status(self):
        for i in range(3):self.store.save({'title':'Title','kind':'code'})
        first=self.request('/api/query',{'limit':1})[1];self.store.save({'title':'new','kind':'code'})
        self.assertEqual(self.request('/api/query',{'limit':1,'cursor':first['nextCursor']})[0],409)
        self.assertEqual(self.request('/api/query',{'limit':1000})[0],400)
        self.assertEqual(self.request('/api/resources/summaries',{'ids':[]})[1]['resources'],[])

if __name__=='__main__':unittest.main()
