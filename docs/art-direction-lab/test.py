import unittest,tempfile,threading,urllib.request,urllib.error,json,sqlite3
from pathlib import Path
import run
class ReviewSafety(unittest.TestCase):
 def test_exact_category_mix_and_saved_records(self):
  with tempfile.TemporaryDirectory() as root:
   store,items=run.dataset(Path(root));self.assertEqual(len(store.state()['resources']),12)
   groups={g:sum(i['group']==g for i in items) for g in {i['group'] for i in items}}
   self.assertEqual(groups,{'开发工具':3,'设计灵感':2,'动效 / 3D':2,'AI / ML':2,'技术文章':1,'代码':1,'Prompt':1})
   self.assertEqual(len({i['resource']['id'] for i in items}),12)
   self.assertTrue(items[6]['resource']['coverId'])
   with sqlite3.connect(store.db) as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
 def test_loopback_read_only_and_whitelist(self):
  http=run.make_server();thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{http.server_port}'
  try:
   before=http.store.state();self.assertEqual(http.server_address[0],'127.0.0.1');self.assertEqual(len(json.load(urllib.request.urlopen(base+'/lab-data'))),12)
   for path in ['/api/resources','/../../desktop-app/data/library.sqlite3','/reference/v3-poster-lab/../../README.md']:
    with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(base+path)
    self.assertEqual(err.exception.code,404)
   for method in ['POST','PUT','PATCH','DELETE']:
    with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(urllib.request.Request(base+'/lab-data',data=b'{}',method=method))
    self.assertEqual(err.exception.code,405)
   self.assertEqual(http.store.state(),before)
  finally:http.shutdown();http.server_close()
if __name__=='__main__':unittest.main()
