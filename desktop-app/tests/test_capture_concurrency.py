import tempfile,unittest,threading
from concurrent.futures import ThreadPoolExecutor
from storage import Store
class CaptureConcurrency(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_parallel_selections_and_duplicate_creation(self):
  page={'url':'https://example.com/parallel','title':'Page'}
  with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda i:self.s.capture_page(page,'selection-%02d-end'%i),range(32)))
  items=self.s.state()['resources'];self.assertEqual(len(items),1)
  for i in range(32):self.assertIn('selection-%02d-end'%i,items[0]['notes'])
  self.assertEqual(sum(not result['alreadySaved'] for result in results),1)
 def test_capture_preserves_concurrent_edits_and_literal_tags(self):
  page={'url':'https://example.com/edit','title':'Browser title'};resource=self.s.capture_page(page)['resource'];rid=resource['id'];gate=threading.Barrier(2)
  def edits():
   gate.wait()
   for i in range(15):self.s.save({'title':'Edited '+str(i),'tags':['New, exact'],'projects':['Current project']},rid)
  def captures():
   gate.wait()
   for i in range(15):self.s.capture_page(page,'Captured %02d'%i)
  with ThreadPoolExecutor(max_workers=2) as pool:
   tasks=[pool.submit(edits),pool.submit(captures)]
   for task in tasks:task.result(timeout=10)
  item=self.s.get(rid);self.assertEqual(item['title'],'Edited 14');self.assertEqual(item['tags'],['New, exact']);self.assertEqual(item['projects'],['Current project'])
  for i in range(15):self.assertIn('Captured %02d'%i,item['notes'])
 def test_capture_restores_trash_without_losing_original_notes(self):
  r=self.s.save({'url':'https://example.com/trash','title':'Original','notes':'Original notes'})['resource'];self.s.remove(r['id']);result=self.s.capture_page({'url':r['url'],'title':'Browser'},'New selection')
  self.assertFalse(result['resource']['deleted']);self.assertEqual(result['resource']['title'],'Original');self.assertIn('Original notes',result['resource']['notes']);self.assertIn('New selection',result['resource']['notes'])
