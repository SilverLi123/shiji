"""Run the shipped JS legacy matcher against actual Store records, not a second oracle."""
import sys,tempfile,unittest,subprocess,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store

class QueryDifferential(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node needed for cross-language differential oracle')
    def test_legacy_filters_agree_with_server(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);store.collection('根');store.collection('子','根')
            for i in range(36):
                r=store.save({'title':('动效 React' if i%2 else '音频 C++')+str(i),'url':'https://'+('sub.' if i%2 else '')+'example.com/'+str(i),'kind':['website','code','prompt','file'][i%4],'category':['开发工具','UI / 设计','音频'][i%3],'tags':['UI','中文'] if i%2 else [],'projects':['子'] if i%3 else [],'projectNotes':{'历史':'保留的备注'} if i%5 else {},'notes':'使用说明' if i%4 else '', 'favorite':bool(i%2),'inbox':bool(i%3),'colors':['#ab12de'] if i%2 else [],'createdAt':'2025-02-03T02:00:00+08:00' if i%2 else '2025-02-04T00:00:00Z'})['resource']
                if i%3==0:store.attachment(r['id'],b'ID3test',{'name':'音效.mp3','colors':['#112233']})
                if i%7==0:store.remove(r['id'])
            filters=[{}, {'search':'React 中文'},{'search':'C++'}, {'tags':['UI','missing'],'tagMode':'any'}, {'tags':['UI'],'excludeTags':['中文']},{'noTags':True},{'noProjects':True},{'hasNotes':True},{'mediaType':'audio'}, {'mediaType':'other'},{'domain':'example.com'},{'domain':'example.com','includeSubdomains':False},{'createdFrom':'2025-02-03','createdTo':'2025-02-03'},{'color':'#ab12de'}, {'color':'#112233'}, {'collection':'根'}, {'category':'UI / 设计','inbox':True},{'favorite':False},{'hasAssets':True},{'isSnippet':True}]
            scopes=['all','trash','assets','snippets','favorite','inbox'];records=[]
            for scope in scopes:
                rows=store.state(scope=='trash')['resources']
                sf={'favorite':True} if scope=='favorite' else {'inbox':True} if scope=='inbox' else {'hasAssets':True} if scope=='assets' else {'isSnippet':True} if scope=='snippets' else {}
                for f in filters:
                    # Match legacy scope first, then all user filters (scope cannot be negated).
                    records.append({'scope':scope,'filter':f,'scopeFilter':sf,'items':rows})
            script="const fs=require('fs'),L=require('./static/library');const v=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(v.cases.map(x=>x.items.filter(r=>L.matches(r,x.scopeFilter,v.meta)&&L.matches(r,x.filter,v.meta)).map(r=>r.id).sort())));"
            result=subprocess.run(['node','-e',script],cwd=Path(__file__).resolve().parents[1],input=json.dumps({'cases':records,'meta':store.state()['collectionMeta']}),text=True,capture_output=True,check=True)
            expected=json.loads(result.stdout)
            for case,ids in zip(records,expected):
                with self.subTest(scope=case['scope'],filters=case['filter']):self.assertEqual(sorted(store.query_ids({'scope':case['scope'],'filters':case['filter']})['ids']),ids)

if __name__=='__main__':unittest.main()
