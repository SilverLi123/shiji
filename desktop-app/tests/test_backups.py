import base64
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store
import backups

class BackupStreams(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
        self.r=self.store.save({'title':'资源','url':'https://example.com/','notes':'保留原备注'})['resource']
        self.a=self.store.attachment(self.r['id'],fixture.PNG,{'name':'封面.png','cover':True})['attachment']
        self.path=self.store.files/self.a['id']
    def tearDown(self):self.temp.cleanup()
    def no_temporary(self):
        self.assertFalse(any(p.name.startswith(('restore-','snapshot-','upload-')) for p in self.store.root.iterdir()))
    def test_disk_backups_do_not_use_whole_file_reads(self):
        with patch.object(self.store,'backup_bytes',side_effect=AssertionError('byte wrapper')),patch.object(Path,'read_bytes',side_effect=AssertionError('whole file')):
            name=self.store.create_backup()['name']
            with self.store.backup_path() as path:
                with zipfile.ZipFile(path) as z:self.assertEqual(z.read('files/'+self.a['id']),fixture.PNG)
        self.assertTrue(self.store.backup_file(name).is_file());self.no_temporary()
    def test_corrupt_and_missing_bytes_repair_existing_identity(self):
        blob=self.store.backup_bytes();before=self.store.state()
        for broken in [b'corrupt',None]:
            if broken is None:self.path.unlink()
            else:self.path.write_bytes(broken)
            result=self.store.restore_zip(blob);self.assertEqual(result['repairedFiles'],1)
            self.assertEqual(self.path.read_bytes(),fixture.PNG);self.assertEqual(self.store.state(),before)
            with zipfile.ZipFile(self.store.backup_file(result['beforeBackup'])) as z:
                manifest=json.loads(z.read('manifest.json'));self.assertEqual(manifest['attachments'],[])
                if broken is not None:
                    self.assertIn(self.a['id'],manifest['damagedFiles']);self.assertEqual(z.read('files/'+self.a['id']),broken)
                else:self.assertIn(self.a['id'],manifest['missingFiles'])
        self.no_temporary()
    def test_symlink_repair_does_not_read_or_change_external_target(self):
        blob=self.store.backup_bytes();external=self.store.root/'external';external.write_bytes(b'private')
        self.path.unlink();self.path.symlink_to(external)
        with self.assertRaises(ValueError):self.store.create_backup()
        result=self.store.restore_zip(blob);self.assertEqual(result['repairedFiles'],1)
        self.assertFalse(self.path.is_symlink());self.assertEqual(self.path.read_bytes(),fixture.PNG);self.assertEqual(external.read_bytes(),b'private');self.no_temporary()
    def test_restore_commit_failure_preserves_bad_bytes_and_missing_state(self):
        blob=self.store.backup_bytes()
        for bad in [b'bad-original',None]:
            if bad is None:self.path.unlink(missing_ok=True)
            else:self.path.write_bytes(bad)
            before=self.store.state();dirty=self.store.dirty;connect=self.store.connect;count=0
            class Failure:
                def __init__(self):self.c=connect()
                def __enter__(self):return self.c
                def __exit__(self,*args):self.c.rollback();self.c.close();raise sqlite3.OperationalError('commit failure')
            def failing():
                nonlocal count
                count+=1
                return connect() if count==1 else Failure()
            with patch.object(self.store,'connect',failing):
                with self.assertRaises(sqlite3.Error):self.store.restore_zip(blob)
            self.assertEqual(self.store.state(),before);self.assertEqual(self.store.dirty,dirty)
            if bad is None:self.assertFalse(self.path.exists())
            else:self.assertEqual(self.path.read_bytes(),bad)
            self.no_temporary()
    def test_validation_error_has_no_files_rows_or_backup_side_effect(self):
        blob=self.store.backup_bytes();before=self.store.state();history=self.store.backup_list()
        for kind in ['hash','path','duplicate','manifest','mime']:
            out=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(blob)) as original,zipfile.ZipFile(out,'w') as bad:
                for name in original.namelist():
                    value=original.read(name)
                    if name=='manifest.json':
                        manifest=json.loads(value)
                        if kind=='hash':manifest['attachments'][0]['sha256']='0'*64
                        if kind=='mime':manifest['attachments'][0]['mime']='audio/wav'
                        if kind=='manifest':manifest=[]
                        value=json.dumps(manifest).encode()
                    bad.writestr(name,value)
                if kind=='path':bad.writestr('../outside',b'x')
                if kind=='duplicate':bad.writestr('manifest.json',b'{}')
            with self.assertRaises(ValueError):self.store.restore_zip(out.getvalue())
            self.assertEqual(self.store.state(),before);self.assertEqual(self.store.backup_list(),history);self.assertEqual(self.path.read_bytes(),fixture.PNG);self.no_temporary()
        with patch.object(backups,'MAX_ARCHIVE',10):
            with self.assertRaises(ValueError):self.store.restore_zip(blob)
        with patch.object(backups,'MAX_MANIFEST',10):
            with self.assertRaises(ValueError):self.store.restore_zip(blob)
        self.no_temporary()
    def test_bad_source_backup_reports_failure_and_does_not_publish_zip(self):
        self.path.write_bytes(b'corrupt');before=list(self.store.backups.iterdir())
        with self.assertRaises(ValueError):self.store.create_backup()
        self.assertEqual(list(self.store.backups.iterdir()),before);self.assertIn('损坏',self.store.backup_list()['warning']);self.no_temporary()
    def test_archive_attachment_reader_is_bounded(self):
        blob=self.store.backup_bytes();reader=zipfile.ZipExtFile.read;calls=[]
        def bounded(stream,n=-1):
            if stream.name.startswith('files/'):
                self.assertGreater(n,0);self.assertLessEqual(n,backups.CHUNK);calls.append(n)
            return reader(stream,n)
        with tempfile.TemporaryDirectory() as d:
            other=Store(d)
            with patch.object(zipfile.ZipExtFile,'read',bounded),patch.object(zipfile.ZipFile,'read',side_effect=AssertionError('whole member read')):
                other.restore_zip(blob)
            self.assertEqual(other.file(self.a['id'])[1].read_bytes(),fixture.PNG)
        self.assertTrue(calls)
    def test_export_rejects_counts_that_its_restore_cannot_accept(self):
        import uuid
        from storage import dump
        for category,count in [('resources',10001),('attachments',20001),('collections',1001),('smartCollections',1001)]:
            with self.subTest(category=category),tempfile.TemporaryDirectory() as directory:
                store=Store(directory)
                with store.connect() as c:
                    if category=='resources':
                        rows=[]
                        for number in range(count):
                            rid=str(uuid.uuid4());item={**self.r,'id':rid,'url':'','kind':'file','attachments':[],'coverId':''}
                            rows.append((rid,'shiji:'+rid,dump(item),0))
                        c.executemany('INSERT INTO resources VALUES(?,?,?,?)',rows)
                    elif category=='attachments':
                        c.execute('INSERT INTO resources VALUES(?,?,?,?)',(self.r['id'],self.r['url'],dump(self.r),0))
                        c.executemany('INSERT INTO attachments VALUES(?,?,?,?)',[(aid,self.r['id'],dump({**self.a,'id':aid}),0) for aid in (str(uuid.uuid4()) for _ in range(count))])
                    elif category=='collections':
                        c.executemany('INSERT INTO collections(name) VALUES(?)',[(str(n),) for n in range(count)])
                    else:
                        c.executemany('INSERT INTO smart_collections VALUES(?,?,?)',[(str(uuid.uuid4()),str(n),'{}') for n in range(count)])
                for emergency in (False,True):
                    with self.assertRaisesRegex(ValueError,'数量限制'):store.create_backup(allow_missing=emergency)
                    self.assertFalse(list(store.backups.iterdir()))
                    self.assertFalse(any(p.name.startswith('snapshot-') for p in store.root.iterdir()))
    def test_project_and_smart_collection_count_boundaries_roundtrip(self):
        import uuid
        with tempfile.TemporaryDirectory() as source_dir,tempfile.TemporaryDirectory() as target_dir:
            source=Store(source_dir);target=Store(target_dir)
            with source.connect() as c:
                c.executemany('INSERT INTO collections(name) VALUES(?)',[(str(n),) for n in range(1000)])
                c.executemany('INSERT INTO smart_collections VALUES(?,?,?)',[(str(uuid.uuid4()),str(n),'{}') for n in range(1000)])
            with source.backup_path() as archive:target.restore_zip(archive)
            self.assertEqual(len(target.state()['collections']),1000)
            self.assertEqual(len(target.state()['smartCollections']),1000)

class StreamHTTP(unittest.TestCase):
    def setUp(self):
        import server
        from http.server import ThreadingHTTPServer
        self.server_module=server;self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);server.STORE=self.store
        self.r=self.store.save({'title':'文件','kind':'file'})['resource'];self.a=self.store.attachment(self.r['id'],fixture.PNG,{'name':'图.png'})['attachment']
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);self.base='http://127.0.0.1:'+str(self.http.server_port)
        self.worker=threading.Thread(target=self.http.serve_forever,daemon=True);self.worker.start()
    def tearDown(self):self.http.shutdown();self.http.server_close();self.worker.join();self.temp.cleanup()
    def request(self,path,raw=None,headers=None):
        req=Request(self.base+path,data=raw,headers=headers or {})
        try:
            with urlopen(req,timeout=15) as r:return r.status,dict(r.headers),r.read()
        except HTTPError as r:return r.code,dict(r.headers),r.read()
    def test_download_restore_and_range_without_whole_reads(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('whole read')),patch.object(self.store,'backup_bytes',side_effect=AssertionError('byte ZIP')):
            status,h,blob=self.request('/api/backup.zip');self.assertEqual(status,200);self.assertEqual(int(h['Content-Length']),len(blob))
            created=self.store.create_backup();self.assertEqual(self.request('/api/backups/'+created['name'])[2][:2],b'PK')
            status,h,value=self.request('/api/files/'+self.a['id'],headers={'Range':'bytes=2-9'})
            self.assertEqual(status,206);self.assertEqual(value,fixture.PNG[2:10]);self.assertEqual(h['Content-Range'],'bytes 2-9/'+str(len(fixture.PNG)))
            self.assertEqual(self.request('/api/files/'+self.a['id'],headers={'Range':'bytes=-4'})[2],fixture.PNG[-4:])
            self.assertEqual(self.request('/api/files/'+self.a['id'],headers={'Range':'bytes=999-'})[0],416)
            self.assertEqual(self.request('/api/files/'+self.a['id'],headers={'Range':'bytes=-0'})[0],416)
            status,h,body=self.request('/api/restore',blob,{'Content-Type':'application/zip'});self.assertEqual(status,200);self.assertEqual(json.loads(body)['skipped'],1)
        self.assertFalse(any(p.name.startswith(('restore-','snapshot-','upload-')) for p in self.store.root.iterdir()))
    def test_invalid_upload_and_origin_leave_data_unchanged(self):
        before=self.store.state()
        self.assertEqual(self.request('/api/restore',b'broken',{'Content-Type':'application/zip'})[0],400)
        self.assertEqual(self.request('/api/restore',b'broken',{'Content-Type':'application/zip','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.store.state(),before)
        self.assertFalse(any(p.name.startswith(('restore-','snapshot-','upload-')) for p in self.store.root.iterdir()))

class RecoveryHTTP(StreamHTTP):
    def test_preflight_cancel_and_confirmation(self):
        blob=self.store.backup_bytes();before=self.store.state()
        status,_,body=self.request('/api/restore/preflight',blob,{'Content-Type':'application/zip'})
        self.assertEqual(status,200);preview=json.loads(body);self.assertEqual(preview['summary']['attachments'],1)
        self.assertEqual(before,self.store.state())
        self.assertEqual(self.request('/api/restore/confirm',json.dumps({'ticket':preview['ticket']}).encode(),{'Content-Type':'application/json'})[0],400)
        self.assertEqual(self.request('/api/restore/cancel',json.dumps({'ticket':preview['ticket']}).encode(),{'Content-Type':'application/json'})[0],200)
        self.assertEqual(before,self.store.state())
        self.assertEqual(self.request('/api/restore/preflight',blob,{'Content-Type':'application/zip','Origin':'https://evil.example'})[0],403)

class PreviewHTTP(StreamHTTP):
    def test_default_off_pause_and_preview_configuration(self):
        status,_,raw=self.request('/api/website-previews');self.assertEqual(status,200);self.assertFalse(json.loads(raw)['enabled'])
        before=self.store.get(self.r['id'])
        status,_,raw=self.request('/api/website-previews',json.dumps({'enabled':True,'paused':True}).encode(),{'Content-Type':'application/json'});self.assertEqual(status,200);self.assertTrue(json.loads(raw)['paused'])
        self.assertEqual(before,self.store.get(self.r['id']))
        self.assertEqual(self.request('/api/website-previews',b'{"interval":1}',{'Content-Type':'application/json'})[0],400)
        self.assertEqual(self.request('/api/website-previews',b'{"enabled":true}',{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
