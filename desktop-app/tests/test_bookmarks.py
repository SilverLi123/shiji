import tempfile
import unittest
from pathlib import Path
import test_upgrade as fixture

def html(body):return '<!DOCTYPE NETSCAPE-Bookmark-file-1><META CHARSET="UTF-8"><DL><p>'+body+'</DL><p>'
def link(url,title='书签',attrs=''):return '<DT><A HREF="'+url+'" '+attrs+'>'+title+'</A>\n'
def folder(name,body):return '<DT><H3>'+name+'</H3><DL><p>'+body+'</DL><p>'

class Bookmarks(unittest.TestCase):
    setUp=fixture.Integration.setUp
    start=fixture.Integration.start
    tearDown=fixture.Integration.tearDown
    req=fixture.Integration.req
    add=fixture.Integration.add
    def preview(self,source,**options):
        body={'html':source,**options};return body,self.req('/api/bookmarks/preview','POST',body)
    def commit(self,body,plan,lines=None,status=200,**options):
        chosen=lines if lines is not None else [i['line'] for i in plan['items'] if i['status']=='new']
        return self.req('/api/bookmarks/import','POST',{**body,'planToken':plan['planToken'],'items':[{'line':n} for n in chosen],**options},status=status)
    def test_folder_duplicates_metadata_and_backup_roundtrip(self):
        source=html(folder('开发 &amp; UI',link('https://NEW.example:443/#first','A &amp; B','ADD_DATE="1609459200" TAGS="React,设计"')+'<DD>原始 <b>描述</b> &amp; 内容\n')+folder('灵感',link('https://new.example/','另一个标题','TAGS="动效"')+'<DD>第二处说明\n'))
        before=self.req('/api/resources');body,plan=self.preview(source)
        self.assertEqual(self.req('/api/resources'),before)
        self.assertEqual([i['status'] for i in plan['items']],['new','duplicate'])
        self.assertEqual(len(plan['items'][0]['projects']),2)
        result=self.commit(body,plan);self.assertEqual(result['added'],1)
        saved=self.req('/api/resources')['resources'][0]
        self.assertEqual(saved['title'],'A & B');self.assertEqual(saved['tags'],['React','设计','动效'])
        self.assertEqual(saved['notes'],'原始 描述 & 内容\n\n第二处说明')
        self.assertEqual(saved['createdAt'],'2021-01-01T00:00:00+00:00');self.assertTrue(saved['inbox'])
        exported=self.req('/api/export');backup=self.req('/api/backup.zip')
        import sys;sys.path.insert(0,str(fixture.APP));from storage import Store
        with tempfile.TemporaryDirectory() as d:
            for kind in ['json','zip']:
                other=Store(Path(d)/kind)
                if kind=='json':other.import_json(exported)
                else:other.restore_zip(backup)
                self.assertEqual(other.state()['collectionMeta'],exported['collectionMeta'])
                row=other.state()['resources'][0]
                for key in ['url','title','notes','tags','projects','createdAt']:self.assertEqual(row[key],saved[key])
    def test_existing_trash_and_dangerous_urls_preserve_originals(self):
        old=self.add(notes='保留',tags=['旧']);trash=self.add(url='https://trash.example/',notes='回收站');self.req('/api/resources/'+trash['id'],'DELETE')
        before=self.req('/api/resources');trash_before=self.req('/api/trash')
        urls=['https://example.com/','https://trash.example/','javascript:alert(1)','data:text/html,evil','file:///tmp/a','mailto:a@example.com','/relative','https://user:password@example.com/']
        body,plan=self.preview(html(''.join(link(u,'<img src=x onerror=evil()>标题') for u in urls)+'<script><a href="https://evil.example/">evil</a></script>'))
        self.assertEqual([i['status'] for i in plan['items']],['existing','trash']+['invalid']*6)
        for n in [1,2,3]:self.commit(body,plan,[n],status=400)
        self.assertEqual(self.req('/api/resources'),before);self.assertEqual(self.req('/api/trash'),trash_before)
        self.assertEqual(old['notes'],'保留')
    def test_folder_description_cannot_overwrite_bookmark_notes(self):
        source=html(link('https://a.example/','A')+'<DD>书签 A 自己的说明\n<DT><H3>文件夹</H3><DD>文件夹说明不属于 A\n<DL><p>'+link('https://b.example/','B')+'<DD>书签 B 自己的说明\n</DL><p>')
        body,plan=self.preview(source)
        self.assertEqual([r['notes'] for r in plan['items']],['书签 A 自己的说明','书签 B 自己的说明'])
        self.assertEqual(plan['items'][1]['folders'],['文件夹'])
        self.commit(body,plan)
        saved={r['title']:r for r in self.req('/api/resources')['resources']}
        self.assertEqual(saved['A']['notes'],'书签 A 自己的说明');self.assertEqual(saved['B']['notes'],'书签 B 自己的说明')
    def test_collisions_only_selected_paths_and_title_override(self):
        self.req('/api/collections','POST',{'name':'浏览器书签','autoTags':['原规则']})
        self.req('/api/collections','POST',{'name':'UI'})
        source=html(folder('开发',folder('UI',link('https://one.example/')))+folder('灵感',folder('UI',link('https://two.example/')))+folder('空目录',''))
        body,plan=self.preview(source);self.assertEqual(plan['rootName'],'浏览器书签（2）')
        self.assertEqual(plan['items'][0]['projectPaths'],['浏览器书签（2） / 开发 / UI（2）'])
        self.commit(body,plan,items=[{'line':1,'title':'改过的名称'}])
        state=self.req('/api/resources');self.assertEqual(state['resources'][0]['title'],'改过的名称')
        self.assertNotIn('灵感',state['collections']);self.assertNotIn('空目录',state['collections'])
        self.assertEqual(next(p for p in state['collectionMeta'] if p['name']=='浏览器书签')['autoTags'],['原规则'])
        self.assertEqual(state['resources'][0]['tags'],[])
    def test_atomic_selection_title_and_combined_tags(self):
        body,plan=self.preview(html(link('https://a.example/')+link('https://b.example/')))
        before=self.req('/api/resources')
        for items in [[{'line':1,'title':'ok'},{'line':2,'title':''}],[{'line':True}],[{'line':1},{'line':1}],[{'line':999}]]:
            self.commit(body,plan,items=items,status=400);self.assertEqual(self.req('/api/resources'),before)
        self.commit(body,plan,items=[{'line':1,'title':'只导入这一条'}]);self.assertEqual(len(self.req('/api/resources')['resources']),1)
        body,plan=self.preview(html(link('https://c.example/',attrs='TAGS="'+','.join('t'+str(i) for i in range(30))+'"')))
        before=self.req('/api/resources');self.commit(body,plan,tags=['额外'],status=400);self.assertEqual(self.req('/api/resources'),before)
    def test_stale_resource_or_project_requires_preview_again(self):
        source=html(link('https://new.example/'))
        for change in ['resource','project','trash']:
            body,plan=self.preview(source)
            if change=='resource':old=self.add(url='https://old.example/')
            elif change=='project':self.req('/api/collections','POST',{'name':'另外项目'})
            else:self.req('/api/resources/'+old['id'],'DELETE')
            before=self.req('/api/resources');self.commit(body,plan,status=400);self.assertEqual(self.req('/api/resources'),before)
        body,plan=self.preview(source);self.commit(body,plan)
    def test_folder_depth_and_many_memberships_can_use_flat_import(self):
        nested=link('https://deep.example/')
        for i in range(10):nested=folder('层'+str(i),nested)
        body,plan=self.preview(html(nested));self.assertEqual(plan['items'][0]['status'],'invalid')
        body,plan=self.preview(html(nested),preserveFolders=False);self.commit(body,plan)
        saved=self.req('/api/resources')['resources'][0];self.assertEqual(saved['projects'],['浏览器书签'])
        source=html(''.join(folder('项目'+str(i),link('https://shared.example/')) for i in range(31)))
        body,plan=self.preview(source);self.assertEqual(plan['items'][0]['status'],'invalid')
        body,plan=self.preview(source,preserveFolders=False);self.commit(body,plan);self.assertEqual(len(self.req('/api/resources')['resources']),2)
    def test_limits_and_metadata_loss_is_visible(self):
        source=html(link('https://long.example/','x'*201,'ADD_DATE="bad" TAGS="'+','.join('t'*51+str(i) for i in range(31))+'"')+'<DD>'+'d'*10001)
        body,plan=self.preview(source);row=plan['items'][0]
        self.assertEqual(len(row['warnings']),4);self.assertEqual(len(row['title']),200);self.assertEqual(len(row['notes']),10000)
        self.commit(body,plan)
        before=self.req('/api/resources')
        for raw in [123,'<html><a href="https://a.example/">ordinary page</a></html>',html(''.join(link('https://n'+str(i)+'.example/') for i in range(2001))),html(link('https://a.example/'))+'中'*(5*1024*1024//3)]:
            self.req('/api/bookmarks/preview','POST',{'html':raw},status=400);self.assertEqual(self.req('/api/resources'),before)
        for values in [{'preserveFolders':'true'},{'rootName':'A,B'}]:self.req('/api/bookmarks/preview','POST',{'html':html(link('https://a.example/')),**values},status=400)
    def test_project_capacity_rolls_back_all_resources(self):
        import sqlite3
        with sqlite3.connect(Path(self.temp.name)/'library.sqlite3') as db:
            db.executemany('INSERT INTO collections(name,parent,auto_tags,archived) VALUES(?,?,?,?)',[(str(i),'','[]',0) for i in range(999)])
        body,plan=self.preview(html(folder('需要子项目',link('https://one.example/'))))
        before=self.req('/api/resources');self.commit(body,plan,status=400);self.assertEqual(self.req('/api/resources'),before)
