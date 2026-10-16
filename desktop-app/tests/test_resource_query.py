import tempfile,unittest,json
from storage import Store

class ResourceQuery(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.store=Store(t.name);self.addCleanup(self.store.stop_search_worker)
    def add(self,title,**values):return self.store.save({'title':title,'kind':'code',**values})['resource']
    def query(self,**kwargs):return self.store.query_resources(kwargs)
    def test_rank_projection_full_detail_and_literal_highlights(self):
        a=self.add('React 动效',snippet='x'*10000+'needle <script>')
        b=self.add('其他',notes='React 动效')
        q=self.query(filters={'search':'react 动效'})
        self.assertEqual([r['id'] for r in q['resources']],[a['id'],b['id']])
        self.assertTrue(q['resources'][0]['_summary']);self.assertLess(len(q['resources'][0]['snippet']),1000)
        self.assertEqual(q['resources'][0]['_highlights']['title'],[[0,5],[6,8]])
        self.assertEqual(len(self.store.get(a['id'])['snippet']),10015)
        q=self.query(filters={'search':'needle'})
        self.assertIn('needle',q['resources'][0]['_excerpt'])
    def test_summary_cannot_be_replayed_as_authoritative_resource(self):
        a=self.add('原文',snippet='完整代码'*500,notes='完整备注'*500)
        projected=self.query()['resources'][0]
        with self.assertRaisesRegex(ValueError,'摘要'):self.store.save(projected,a['id'])
        self.assertEqual(self.store.get(a['id']),a)

    def test_pages_stable_ties_query_binding_and_revision_conflicts(self):
        from resource_query import QueryConflict
        for i in range(9):self.add('同名',createdAt='2025-01-01T00:00:00Z')
        first=self.query(limit=3,sort='name');second=self.query(limit=3,sort='name',cursor=first['nextCursor'])
        self.assertFalse({r['id'] for r in first['resources']}&{r['id'] for r in second['resources']})
        with self.assertRaises(QueryConflict):self.query(limit=3,sort='new',cursor=first['nextCursor'])
        self.add('新增')
        with self.assertRaises(QueryConflict):self.query(limit=3,sort='name',cursor=first['nextCursor'])
    def test_hierarchy_smart_scope_and_combined_filters(self):
        self.store.collection('根');self.store.collection('子','根')
        a=self.add('组件',projects=['子'],tags=['UI','组件'],projectNotes={'子':'备注'},favorite=True)
        b=self.add('组件 two',tags=['组件']);self.store.remove(b['id'])
        smart=self.store.smart({'name':'我的','filters':{'tags':['UI']}})
        q=self.query(filters={'collection':'根','hasNotes':True,'tags':['UI','组件']},scope='favorite')
        self.assertEqual([r['id'] for r in q['resources']],[a['id']])
        self.assertEqual(self.query(scope='trash')['total'],1)
        self.assertEqual(self.query(scope='smart',scopeValue=smart['id'])['total'],1)
        meta=self.store.library_metadata();self.assertEqual(meta['projectCounts']['根'],1);self.assertEqual(meta['counts']['trash'],1)
    def test_explicit_filters_can_remove_original_scope_and_smart_conditions(self):
        self.add('甲',category='开发工具',notes='有备注');self.add('乙',category='其他')
        smart=self.store.smart({'name':'备注','filters':{'hasNotes':True}})
        self.assertEqual(self.query(scope='smart',scopeValue=smart['id'])['total'],1)
        self.assertEqual(self.query(scope='smart',scopeValue=smart['id'],filters={})['total'],2)
        self.assertEqual(self.query(scope='category',scopeValue='开发工具')['total'],1)
        self.assertEqual(self.query(scope='category',scopeValue='开发工具',filters={'category':''})['total'],2)

    def test_all_match_selection_and_guarded_batch_is_atomic(self):
        from resource_query import QueryConflict
        for i in range(12):self.add('select '+str(i))
        ids=self.store.query_ids({'filters':{'search':'select'},'limit':2})
        self.assertEqual(len(ids['ids']),12)
        self.store.query_batch({'operation':'batch','revision':ids['revision'],'body':{'ids':ids['ids'],'action':'organized'}})
        with self.assertRaises(QueryConflict):self.store.query_batch({'operation':'batch','revision':ids['revision'],'body':{'ids':ids['ids'],'action':'delete'}})
        self.assertEqual(self.query()['total'],12)
    def test_delete_restore_attachment_rebuild_and_cancelled_cursor(self):
        a=self.add('音效',notes='unusual')
        self.store.attachment(a['id'],b'ID3test',{'name':'Sound.mp3'})
        self.assertEqual(self.query(filters={'search':'Sound','mediaType':'audio'})['total'],1)
        self.store.remove(a['id']);self.assertEqual(self.query(filters={'search':'Sound'})['total'],0)
        self.store.remove(a['id'],True);self.assertEqual(self.query(filters={'search':'Sound'})['total'],1)
        with self.store.connect() as c:c.execute('DROP TABLE search_fts')
        self.assertEqual(self.query(filters={'search':'Sound'})['total'],1)
    def test_media_anchor_preserves_full_match_order_and_all_owner_attachments(self):
        ids=[]
        for i in range(130):
            r=self.add('Audio '+str(i).zfill(3));ids.append(r['id'])
            self.store.attachment(r['id'],b'ID3test',{'name':'音效.mp3'})
        page=self.query(sort='name',mediaOnly=True,projection='media',anchor=ids[125])
        self.assertEqual(page['resources'][5]['id'],ids[125]);self.assertEqual(page['total'],130)
        previous=self.query(sort='name',mediaOnly=True,projection='media',cursor=page['previousCursor'])
        self.assertEqual(previous['resources'][0]['id'],ids[60])
        self.assertEqual(previous['resources'][-1]['id'],ids[119])
        self.assertIsNotNone(previous['nextCursor'])

    def test_validation_and_bounded_ids_summary(self):
        for q in ({'limit':0},{'limit':101},{'scope':'evil'},{'filters':{'search':'x'*201}},{'cursor':'garbage'},{'sort':'sql'}):
            with self.assertRaises(ValueError):self.query(**q)
        a=self.add('正常');self.assertEqual(self.store.resource_summaries({'ids':[a['id']]})['resources'][0]['id'],a['id'])

if __name__=='__main__':unittest.main()
