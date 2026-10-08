"""Real HTTP integration tests. All data lives in disposable directories."""
import base64
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
APP=Path(__file__).resolve().parents[1]
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jz1cAAAAASUVORK5CYII=')
class Integration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.start()
    def start(self):
        self.proc=subprocess.Popen([sys.executable,str(APP/'server.py'),'--port','0','--data-dir',self.temp.name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        line=self.proc.stdout.readline();self.assertIn('http://',line)
        self.base=re.search(r'http://\S+',line).group()
    def tearDown(self):
        self.proc.terminate();self.proc.wait(timeout=5);self.proc.stdout.close();self.proc.stderr.close();self.temp.cleanup()
    def req(self,path,method='GET',data=None,status=200,raw=None,headers=None):
        h={'Content-Type':'application/json'};h.update(headers or {})
        req=Request(self.base+path,method=method,headers=h,data=raw if raw is not None else json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(req,timeout=15) as r:code,body=r.status,r.read()
        except HTTPError as e:code,body=e.code,e.read()
        self.assertEqual(code,status,(path,body[:500]));return body if raw is not None or path.endswith('.zip') or path.startswith('/api/files/') or path.startswith('/api/backups/') else json.loads(body)
    def add(self,**kwargs):
        return self.req('/api/resources','POST',{'url':'https://example.com/','title':'资源',**kwargs})['resource']
    def test_repeated_capture_keeps_new_selection_and_ignores_optional_data_icon(self):
        token=self.req('/api/pairing')['token'];headers={'Authorization':'Bearer '+token}
        first=self.req('/api/clip','POST',{'url':'https://example.com/','title':'页面','selection':'first passage','favicon':'data:image/svg+xml;base64,PHN2Zy8+'},headers=headers)
        second=self.req('/api/clip','POST',{'url':'https://example.com/','selection':'second passage'},headers=headers)
        self.assertEqual(first['resource']['id'],second['resource']['id']);self.assertIn('first passage',second['resource']['notes']);self.assertIn('second passage',second['resource']['notes'])
        self.assertEqual(second['resource']['favicon'],'');self.assertTrue(second['contentAdded'])
    def test_invalid_capture_screenshot_does_not_create_resource(self):
        token=self.req('/api/pairing')['token']
        self.req('/api/clip','POST',{'url':'https://example.com/','screenshot':'invalid'},headers={'Authorization':'Bearer '+token},status=400)
        self.assertEqual(self.req('/api/resources')['resources'],[])
    def test_multiple_projects_survive_edit_and_restart(self):
        item=self.add(projects=['甲','乙'],projectNotes={'甲':'首页参考','乙':'动效'})
        self.assertEqual(item.get('projects'),['甲','乙'])
        self.req('/api/resources/'+item['id'],'PUT',{**item,'title':'修改'})
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close();self.start()
        item=self.req('/api/resources')['resources'][0]
        self.assertEqual(item['projectNotes']['甲'],'首页参考');self.assertEqual(item['projects'],['甲','乙'])
    def test_trash_restores_original_resource(self):
        item=self.add();self.req('/api/resources/'+item['id'],'DELETE')
        self.assertEqual(self.req('/api/resources')['resources'],[])
        self.assertEqual(self.req('/api/trash')['resources'][0]['id'],item['id'])
        self.req('/api/resources/'+item['id']+'/restore','POST',{})
        self.assertEqual(self.req('/api/resources')['resources'][0]['id'],item['id'])
    def test_batch_atomic_and_shared_project(self):
        a=self.add();b=self.add(url='https://second.example/')
        self.req('/api/batch','POST',{'ids':[a['id'],b['id']],'action':'tags','tags':['动效']})
        self.req('/api/batch','POST',{'ids':[a['id'],'missing'],'action':'projects','projects':['甲']},status=400)
        rows=self.req('/api/resources')['resources'];self.assertTrue(all(x['tags']==['动效'] and not x['projects'] for x in rows))
        self.req('/api/batch','POST',{'ids':[a['id'],b['id']],'action':'projects','projects':['甲','乙']})
        self.assertTrue(all(x['projects']==['甲','乙'] for x in self.req('/api/resources')['resources']))
    def test_tag_merge_preserves_unique_tags(self):
        self.add(tags=['React','react','动效'])
        self.req('/api/tags','POST',{'from':'react','to':'React'})
        self.assertEqual(self.req('/api/resources')['resources'][0]['tags'],['React','动效'])
    def test_saved_filters_persist(self):
        self.req('/api/smart-collections','POST',{'name':'React 动效','filters':{'tags':['React','动效'],'kind':'website'}})
        smart=self.req('/api/resources')['smartCollections'];self.assertEqual(smart[0]['filters']['tags'],['React','动效'])
    def test_old_collection_migrates_to_projects(self):
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close()
        with sqlite3.connect(Path(self.temp.name)/'library.sqlite3') as db:
            db.execute("PRAGMA user_version=0")
            db.execute("INSERT INTO resources(id,url,payload) VALUES(?,?,?)",('old','https://old.example/',json.dumps({'id':'old','title':'旧收藏','url':'https://old.example/','collection':'旧项目','tags':[],'createdAt':'2020-01-01T00:00:00+00:00','updatedAt':'2020-01-01T00:00:00+00:00'})))
        self.start();old=self.req('/api/resources')['resources'][0];self.assertEqual(old.get('projects'),['旧项目'])
    def test_file_without_url_and_snippet_roundtrip(self):
        file=self.add(url='',kind='file',title='音效');self.assertEqual(file['url'],'')
        code=self.add(url='',kind='code',title='组件',snippet='const value = 1;',language='javascript')
        self.assertEqual(code.get('snippet'),'const value = 1;')
        self.assertEqual(len(self.req('/api/export')['resources']),2)
    def test_cross_origin_mutation_rejected(self):
        self.req('/api/resources','POST',{'url':'https://example.com/','title':'bad'},status=403,headers={'Origin':'https://evil.example'})
    def upload(self,rid,data=PNG,meta=None):
        h={'Content-Type':'application/octet-stream','X-Metadata':base64.b64encode(json.dumps(meta or {'name':'截图.png','cover':True,'colors':['#268bd2']}).encode()).decode()}
        return json.loads(self.req('/api/resources/'+rid+'/attachments','POST',raw=data,headers=h))['attachment']
    def test_attachment_cover_and_provenance_survive_restart(self):
        r=self.add();a=self.upload(r['id'],meta={'name':'截图.png','cover':True,'colors':['#268bd2'],'author':'作者','sourceUrl':'https://source.example/','license':'需署名'})
        self.assertEqual(self.req('/api/files/'+a['id']),PNG)
        r=self.req('/api/resources')['resources'][0];self.assertEqual(r['coverId'],a['id']);self.assertEqual(r['colors'],['#268bd2']);self.assertEqual(r['attachments'][0]['author'],'作者')
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close();self.start()
        self.assertEqual(self.req('/api/files/'+a['id']),PNG)
    def test_upload_to_deleted_resource_rejected(self):
        r=self.add();self.req('/api/resources/'+r['id'],'DELETE')
        self.req('/api/resources/'+r['id']+'/attachments','POST',raw=PNG,status=400,headers={'Content-Type':'application/octet-stream'})
    def test_untrusted_html_stays_download_only(self):
        r=self.add(kind='file',url='');a=self.upload(r['id'],b'<script>alert(1)</script>',{'name':'unsafe.html'})
        self.assertEqual(a['mime'],'application/octet-stream')
        with urlopen(self.base+'/api/files/'+a['id']) as response:self.assertIn('attachment',response.headers['Content-Disposition'])
    def test_media_range_and_linked_prompt_preserve_content(self):
        r=self.add();wav=b'RIFF'+bytes(4)+b'WAVE'+b'x'*64;a=self.upload(r['id'],wav,{'name':'audio.wav'})
        with urlopen(Request(self.base+'/api/files/'+a['id'],headers={'Range':'bytes=12-19'})) as response:
            self.assertEqual(response.status,206);self.assertEqual(response.read(),wav[12:20]);self.assertEqual(response.headers['Content-Type'],'audio/wav')
        prompt=self.add(url='',kind='prompt',title='提示词',parentId=r['id'],snippet='设计一个首页')
        self.assertEqual(prompt['parentId'],r['id']);self.assertEqual(prompt['snippet'],'设计一个首页')
    def test_complete_backup_restores_attachment_and_projects(self):
        r=self.add(projects=['项目'],projectNotes={'项目':'参考'});a=self.upload(r['id'])
        blob=self.req('/api/backup.zip')
        with zipfile.ZipFile(io.BytesIO(blob)) as z:self.assertIn('library.sqlite3',z.namelist());self.assertEqual(z.read('files/'+a['id']),PNG)
        self.req('/api/resources/'+r['id'],'DELETE')
        result=json.loads(self.req('/api/restore','POST',raw=blob,headers={'Content-Type':'application/zip'}))
        self.assertEqual(result['restored'],1);r=self.req('/api/resources')['resources'][0];self.assertEqual(r['projectNotes']['项目'],'参考');self.assertEqual(self.req('/api/files/'+a['id']),PNG)
    def test_corrupted_zip_leaves_existing_data_untouched(self):
        r=self.add();a=self.upload(r['id']);blob=self.req('/api/backup.zip');bad=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(blob)) as src,zipfile.ZipFile(bad,'w') as dst:
            for name in src.namelist():dst.writestr(name,b'bad' if name.startswith('files/') else src.read(name))
        self.req('/api/restore','POST',raw=bad.getvalue(),status=400,headers={'Content-Type':'application/zip'})
        self.assertEqual(self.req('/api/resources')['resources'][0]['id'],r['id']);self.assertEqual(self.req('/api/files/'+a['id']),PNG)
    def test_zip_paths_cannot_escape_library(self):
        bad=io.BytesIO()
        with zipfile.ZipFile(bad,'w') as z:z.writestr('../escape','no');z.writestr('manifest.json','{}')
        self.req('/api/restore','POST',raw=bad.getvalue(),status=400,headers={'Content-Type':'application/zip'})
        self.assertFalse((Path(self.temp.name).parent/'escape').exists())
    def test_automatic_and_manual_backups_are_recoverable(self):
        self.assertGreaterEqual(len(self.req('/api/backups')['snapshots']),1)
        self.assertEqual(self.req('/api/backups')['backups'],[],'startup must not produce a full ZIP')
        self.add();created=self.req('/api/backups','POST',{})
        self.assertIn(created['name'],[b['name'] for b in self.req('/api/backups')['backups']])
        blob=self.req('/api/backups/'+created['name'])
        with zipfile.ZipFile(io.BytesIO(blob if isinstance(blob,bytes) else b'')) as z:self.assertEqual(json.loads(z.read('manifest.json'))['resources'][0]['title'],'资源')
    def test_browser_clip_requires_pairing_and_saves_screenshot(self):
        self.req('/api/clip','POST',{'url':'https://example.com/','title':'扩展收藏'},status=403)
        token=self.req('/api/pairing')['token'];headers={'Authorization':'Bearer '+token,'Origin':'chrome-extension://'+'a'*32}
        r=self.req('/api/clip','POST',{'url':'https://example.com/','title':'扩展收藏','screenshot':'data:image/png;base64,'+base64.b64encode(PNG).decode()},headers=headers)['resource']
        self.assertEqual(r['title'],'扩展收藏');self.assertTrue(r['coverId']);self.assertEqual(self.req('/api/files/'+r['coverId']),PNG)
        again=self.req('/api/clip','POST',{'url':r['url'],'title':'重复'},headers=headers);self.assertTrue(again['alreadySaved']);self.assertEqual(len(self.req('/api/resources')['resources']),1)
    def test_private_metadata_fails_without_blocking_save(self):
        self.assertEqual(self.req('/api/metadata','POST',{'url':'http://127.0.0.1/'})['status'],'unknown')
        self.assertTrue(self.add()['id'])
    def test_private_link_is_unknown_and_saved_status_persists(self):
        r=self.add(url='http://127.0.0.1/')
        results=self.req('/api/check-links','POST',{'ids':[r['id']]})['results'];self.assertEqual(results[0]['status'],'unknown')
        self.assertEqual(self.req('/api/resources')['resources'][0]['linkStatus'],'unknown')
