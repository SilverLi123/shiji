import base64
import json
import sqlite3
import time
import unittest
from pathlib import Path
import test_upgrade as fixture

class Health(unittest.TestCase):
    setUp=fixture.Integration.setUp;start=fixture.Integration.start;tearDown=fixture.Integration.tearDown;req=fixture.Integration.req;add=fixture.Integration.add
    def upload(self,r,raw=fixture.PNG,**meta):
        data={'name':'sample.png',**meta};headers={'X-Metadata':base64.b64encode(json.dumps(data).encode()).decode()}
        return json.loads(self.req('/api/resources/'+r['id']+'/attachments','POST',raw=raw,headers=headers))
    def scan(self):
        self.req('/api/library-health','POST',{})
        for _ in range(200):
            status=self.req('/api/library-health')
            if status['status']!='running':self.assertEqual(status['status'],'complete');return status['report']
            time.sleep(.01)
        self.fail('Scan did not finish')
    def test_identical_upload_reuses_only_same_resource_and_metadata(self):
        a=self.add();first=self.upload(a,cover=True);second=self.upload(a,cover=True)
        self.assertTrue(second['reused']);self.assertEqual(first['attachment']['id'],second['attachment']['id'])
        self.assertEqual(len(self.req('/api/resources')['resources'][0]['attachments']),1)
        different=self.upload(a,author='different');self.assertFalse(different['reused'])
        other=self.add(url='https://other.example/');self.assertFalse(self.upload(other)['reused'])
        report=self.scan();self.assertEqual(len(report['duplicates']),1);self.assertEqual(len(report['duplicates'][0]['items']),3)
    def test_bad_existing_copy_is_not_reused(self):
        a=self.add();first=self.upload(a)['attachment'];path=Path(self.temp.name)/'files'/first['id']
        path.write_bytes(b'corrupt');next_copy=self.upload(a);self.assertFalse(next_copy['reused'])
        report=self.scan();self.assertEqual(report['issues'][0]['reason'],'corrupt');self.assertEqual(report['duplicates'],[])
        path.unlink()
        # An intact later copy remains reusable despite a missing older copy.
        self.assertTrue(self.upload(a)['reused'])
        self.assertEqual(self.scan()['issues'][0]['reason'],'missing')
    def test_only_missing_copy_is_replaced_and_symlink_is_not_read(self):
        a=self.add();first=self.upload(a)['attachment'];path=Path(self.temp.name)/'files'/first['id'];path.unlink()
        self.assertFalse(self.upload(a)['reused'])
        outside=Path(self.temp.name)/'private.bin';outside.write_bytes(fixture.PNG);path.symlink_to(outside)
        report=self.scan();self.assertEqual(report['issues'][0]['reason'],'unreadable');self.assertEqual(report['presentFiles'],1)
    def test_recovering_missing_bytes_marks_old_report_stale(self):
        a=self.add();first=self.upload(a)['attachment'];backup=self.req('/api/backup.zip')
        path=Path(self.temp.name)/'files'/first['id'];path.unlink()
        report=self.scan();self.assertFalse(report['stale']);self.assertEqual(report['issues'][0]['reason'],'missing')
        self.req('/api/restore','POST',raw=backup)
        self.assertEqual(path.read_bytes(),fixture.PNG)
        self.assertTrue(self.req('/api/library-health')['report']['stale'])
        fresh=self.scan();self.assertFalse(fresh['stale']);self.assertEqual(fresh['issues'],[])
    def test_scan_is_read_only_and_trash_is_distinguished(self):
        a=self.add();b=self.add(url='https://trash.example/');x=self.upload(a)['attachment'];y=self.upload(b)['attachment']
        self.req('/api/resources/'+b['id'],'DELETE');(Path(self.temp.name)/'files'/y['id']).unlink()
        (Path(self.temp.name)/'files'/'unregistered.bin').write_bytes(b'leftover')
        before=self.req('/api/resources');trash=self.req('/api/trash');report=self.scan()
        self.assertEqual(report['duplicates'],[]);self.assertEqual(report['issues'][0]['id'],y['id']);self.assertTrue(report['issues'][0]['inTrash'])
        self.assertEqual(report['unregisteredFiles'],['unregistered.bin']);self.assertFalse(report['stale'])
        self.assertEqual(self.req('/api/resources'),before);self.assertEqual(self.req('/api/trash'),trash)
        self.req('/api/resources/'+a['id'],'PUT',{**a,'title':'renamed'})
        self.assertTrue(self.req('/api/library-health')['report']['stale'])
    def test_health_requests_keep_origin_protection_and_validate_cancel(self):
        self.req('/api/library-health','POST',{},headers={'Origin':'https://evil.example'},status=403)
        self.req('/api/library-health','POST',{'cancel':'yes'},status=400)
        self.assertEqual(self.req('/api/library-health')['status'],'idle')
        self.req('/api/library-health/report',status=400)
        self.add();report=self.scan();export=self.req('/api/library-health/report')
        self.assertEqual(export,report)
    def test_reused_attachment_backup_roundtrip_has_one_identity(self):
        a=self.add();first=self.upload(a,cover=True)['attachment'];self.upload(a,cover=True)
        blob=self.req('/api/backup.zip')
        import tempfile,sys
        sys.path.insert(0,str(fixture.APP));from storage import Store
        with tempfile.TemporaryDirectory() as d:
            store=Store(d);store.restore_zip(blob);r=store.state()['resources'][0]
            self.assertEqual(len(r['attachments']),1);self.assertEqual(r['coverId'],first['id']);self.assertEqual(store.file(first['id'])[1].read_bytes(),fixture.PNG)

class Background(unittest.TestCase):
    def test_scan_releases_library_lock_and_can_cancel(self):
        import tempfile,sys,threading
        from unittest.mock import patch
        sys.path.insert(0,str(fixture.APP));from storage import Store
        from health import HealthOperations
        with tempfile.TemporaryDirectory() as d:
            store=Store(d);r=store.save({'title':'file','kind':'file','url':''})['resource'];store.attachment(r['id'],fixture.PNG,{'name':'a.png'})
            entered=threading.Event();release=threading.Event();original=Path.open
            def blocked(path,*args,**kwargs):
                if path.parent==store.files:entered.set();release.wait(3)
                return original(path,*args,**kwargs)
            with patch.object(Path,'open',blocked):
                started=store.start_health();self.assertTrue(entered.wait(2))
                self.assertEqual(store.start_health()['jobId'],started['jobId'])
                store.save({'title':'still responsive','kind':'file','url':''})
                store.start_health(True);release.set()
                for _ in range(100):
                    if store.health_status()['status']!='running':break
                    time.sleep(.01)
                self.assertEqual(store.health_status()['status'],'cancelled');self.assertEqual(len(store.state()['resources']),2)
