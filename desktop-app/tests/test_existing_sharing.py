import io
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import test_upgrade as fixture
import test_health
sys.path.insert(0,str(fixture.APP))
from storage import Store

class ExistingSharing(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def add(self,title,raw=fixture.PNG):
        resource=self.store.save({'kind':'file','title':title,'category':'美术素材','license':'待确认'})['resource']
        return self.store.attachment(resource['id'],raw,{'name':title+'.png','author':title,'sourceUrl':'https://example.com/'+title,'license':'待确认','cover':True})['attachment']
    def independent(self,a):
        path=self.store.files/a['id'];other=path.with_suffix('.copy');other.write_bytes(path.read_bytes());os.replace(other,path)
    def scan(self):
        self.store.start_health()
        for _ in range(400):
            s=self.store.health_status()
            if s['status']!='running':self.assertEqual(s['status'],'complete');return s
            time.sleep(.005)
        self.fail('scan timeout')
    def group(self,n=3):
        items=[self.add(str(i)) for i in range(n)]
        for a in items:self.independent(a)
        return items,self.scan()
    def start(self,s):return self.store.start_sharing({'scanJobId':s['jobId'],'sha256':s['report']['duplicates'][0]['sha256']})
    def wait(self,status='complete'):
        for _ in range(400):
            s=self.store.health_status()['sharing']
            if s['status']!='running':self.assertEqual(s['status'],status,s);return s
            time.sleep(.005)
        self.fail('sharing timeout')
    def assert_originals(self,items,before,inodes):
        self.assertEqual(self.store.state(),before)
        for a,inode in zip(items,inodes):
            p=self.store.files/a['id'];self.assertEqual(p.read_bytes(),fixture.PNG);self.assertEqual(p.stat().st_ino,inode)
        self.assertEqual(list(self.store.files.glob('.share-*')),[])
    def test_existing_group_shares_bytes_preserves_payloads_and_backup(self):
        items,s=self.group();before=self.store.state();self.assertEqual(s['report']['duplicates'][0]['storedCopies'],3)
        self.start(s);job=self.wait();self.assertEqual(job['changedFiles'],2);self.assertEqual(job['sharedBytes'],2*len(fixture.PNG));self.assertEqual(self.store.state(),before)
        self.assertEqual(len({(self.store.files/a['id']).stat().st_ino for a in items}),1)
        with zipfile.ZipFile(self.store.backups/job['backup']['name']) as z:
            for a in items:self.assertEqual(z.read('files/'+a['id']),fixture.PNG)
            self.assertEqual(json.loads(z.read('manifest.json'))['version'],2)
        self.assertTrue(self.store.health_status()['report']['stale'])
        fresh=self.scan();self.assertEqual(fresh['report']['duplicates'][0]['storedCopies'],1);self.assertEqual(fresh['report']['sharedBytes'],2*len(fixture.PNG))
        with self.assertRaises(ValueError):self.start(fresh)
    def test_stale_scan_cancelled_scan_and_wrong_group_cannot_write(self):
        items,s=self.group();before=self.store.state();inodes=[(self.store.files/a['id']).stat().st_ino for a in items]
        for body in [{},{'scanJobId':s['jobId'],'sha256':'../bad'},{'scanJobId':'wrong','sha256':s['report']['duplicates'][0]['sha256']},{'scanJobId':s['jobId'],'sha256':'0'*64},{'cancel':True,'jobId':'wrong'},{'cancel':'yes'}]:
            with self.assertRaises(ValueError):self.store.start_sharing(body)
        self.store.health_state['status']='cancelled'
        with self.assertRaises(ValueError):self.start(s)
        self.store.health_state['status']='complete';self.independent(items[0])
        with self.assertRaises(ValueError):self.start(s)
        self.assertEqual(self.store.state(),before);self.assertEqual(list(self.store.files.glob('.share-*')),[])
    def test_failed_backup_and_unsupported_links_preserve_original_paths(self):
        for failure in ['backup','link']:
            with self.subTest(failure=failure):
                items,s=self.group();before=self.store.state();inodes=[(self.store.files/a['id']).stat().st_ino for a in items]
                target=patch.object(self.store,'create_backup',side_effect=OSError('disk full')) if failure=='backup' else patch('maintenance.os.link',side_effect=OSError('unsupported'))
                with target:self.start(s);self.wait('failed')
                self.assert_originals(items,before,inodes)
                # Fresh report includes previous groups too, but no destructive fallback.
    def test_publish_failure_rolls_back_all_replaced_inodes(self):
        items,s=self.group();before=self.store.state();inodes=[(self.store.files/a['id']).stat().st_ino for a in items];original=os.replace;calls=0
        def replace(source,destination):
            nonlocal calls
            if str(source).endswith('.new'):
                calls+=1
                if calls==2:raise OSError('injected publish failure')
            return original(source,destination)
        with patch('maintenance.os.replace',side_effect=replace):self.start(s);self.wait('failed')
        self.assert_originals(items,before,inodes)
    def test_cancel_while_publishing_rolls_back_and_status_stays_responsive(self):
        items,s=self.group();before=self.store.state();inodes=[(self.store.files/a['id']).stat().st_ino for a in items]
        entered=threading.Event();release=threading.Event();original=os.replace
        def replace(source,destination):
            result=original(source,destination)
            if str(source).endswith('.new') and not entered.is_set():entered.set();release.wait(3)
            return result
        with patch('maintenance.os.replace',side_effect=replace):
            self.start(s);self.assertTrue(entered.wait(2));started=time.monotonic();current=self.store.health_status();self.assertLess(time.monotonic()-started,.2)
            with self.assertRaises(ValueError):self.store.start_health()
            with self.assertRaises(ValueError):self.start(s)
            self.store.start_sharing({'cancel':True,'jobId':current['sharing']['jobId']});release.set();self.wait('cancelled')
        self.assert_originals(items,before,inodes)
    def test_trash_and_unrelated_inodes_are_not_replaced_or_overcounted(self):
        items,_=self.group();trash_items=[self.add('trash1'),self.add('trash2')]
        old_inodes=[]
        for item,target in zip(trash_items,items[1:]):
            p=self.store.files/item['id'];p.unlink();os.link(self.store.files/target['id'],p);old_inodes.append(p.stat().st_ino)
            self.store.remove(item['resourceId'])
        before=self.store.state();trash_before=self.store.state(trash=True)
        s=self.scan();self.start(s);job=self.wait()
        self.assertEqual(job['changedFiles'],2);self.assertEqual(job['sharedBytes'],len(fixture.PNG),'one old inode remains owned by trash, so do not count it as removed')
        for item,inode in zip(trash_items,old_inodes):
            p=self.store.files/item['id'];self.assertEqual(p.stat().st_ino,inode);self.assertEqual(p.read_bytes(),fixture.PNG)
        self.assertEqual(self.store.state(),before);self.assertEqual(self.store.state(trash=True),trash_before)
    def test_partial_cleanup_failure_reports_committed_sharing_honestly(self):
        items,s=self.group();before=self.store.state();original=__import__('shutil').rmtree
        def cleanup(path,*args,**kwargs):
            if Path(path).name.startswith('.share-'):
                old=next(Path(path).glob('*.old'));old.unlink();raise OSError('partial cleanup')
            return original(path,*args,**kwargs)
        with patch('maintenance.shutil.rmtree',side_effect=cleanup):self.start(s);job=self.wait()
        self.assertEqual(job['changedFiles'],2);self.assertEqual(job['sharedBytes'],2*len(fixture.PNG));self.assertIn('cleanupWarning',job)
        self.assertEqual(len({(self.store.files/a['id']).stat().st_ino for a in items}),1);self.assertEqual(self.store.state(),before)
        self.assertTrue((self.store.files/job['recoveryDirectory']).is_dir());self.assertTrue((self.store.backups/job['backup']['name']).is_file())
    def test_late_cancel_during_cleanup_does_not_promise_rollback(self):
        items,s=self.group();entered=threading.Event();release=threading.Event();original=__import__('shutil').rmtree
        def cleanup(path,*args,**kwargs):
            if Path(path).name.startswith('.share-'):entered.set();release.wait(3)
            return original(path,*args,**kwargs)
        try:
            with patch('maintenance.shutil.rmtree',side_effect=cleanup):
                self.start(s);self.assertTrue(entered.wait(2));current=self.store.health_status()['sharing'];self.assertEqual(current['phase'],'cleanup')
                response=self.store.start_sharing({'cancel':True,'jobId':current['jobId']})
                self.assertFalse(response['sharing']['cancelRequested']);self.assertFalse(self.store.share_cancel.is_set());release.set();job=self.wait()
            self.assertEqual(job['changedFiles'],2);self.assertEqual(len({(self.store.files/a['id']).stat().st_ino for a in items}),1)
        finally:release.set()
    def test_status_snapshot_race_never_waits_for_worker_storage_lock(self):
        items,s=self.group();lock=self.store.lock;status_entered=threading.Event();resume_status=threading.Event();backup_entered=threading.Event();resume_backup=threading.Event();done=threading.Event();answers=[]
        class GateLock:
            def acquire(self,*args,**kwargs):
                if threading.current_thread().name=='racing-status':status_entered.set();resume_status.wait(3)
                return lock.acquire(*args,**kwargs)
            def release(self):return lock.release()
            def __enter__(self):self.acquire();return self
            def __exit__(self,*args):self.release()
        self.store.lock=GateLock();backup=self.store.create_backup
        def paused_backup(*args,**kwargs):backup_entered.set();resume_backup.wait(3);return backup(*args,**kwargs)
        def status():answers.append(self.store.health_status());done.set()
        reader=threading.Thread(target=status,name='racing-status');reader.start()
        try:
            self.assertTrue(status_entered.wait(1))
            with patch.object(self.store,'create_backup',side_effect=paused_backup):
                self.start(s);self.assertTrue(backup_entered.wait(1));resume_status.set()
                self.assertTrue(done.wait(.3),'status must not wait for the background job storage lock')
                self.assertEqual(answers[0]['sharing']['status'],'running');resume_backup.set();self.wait()
        finally:resume_status.set();resume_backup.set();reader.join(3);self.store.lock=lock
    def test_prepared_bytes_or_paths_changing_are_rejected(self):
        items,s=self.group();before=self.store.state();original=os.link
        def link(source,dest,**kwargs):
            result=original(source,dest,**kwargs)
            if str(dest).endswith('.new'):
                Path(dest).unlink();Path(dest).write_bytes(b'different')
            return result
        with patch('maintenance.os.link',side_effect=link):self.start(s);self.wait('failed')
        self.assertEqual(self.store.state(),before)
        for a in items:self.assertEqual((self.store.files/a['id']).read_bytes(),fixture.PNG)
        self.assertEqual(list(self.store.files.glob('.share-*')),[])

class SharingHTTP(unittest.TestCase):
    setUp=fixture.Integration.setUp;tearDown=fixture.Integration.tearDown;start=fixture.Integration.start;req=fixture.Integration.req;add=fixture.Integration.add;upload=test_health.Health.upload;scan=test_health.Health.scan
    def test_origin_validation_real_job_and_independent_downloads(self):
        a=self.add();b=self.add(url='https://second.example/');x=self.upload(a)['attachment'];y=self.upload(b,author='another')['attachment']
        p=Path(self.temp.name)/'files'/y['id'];tmp=p.with_suffix('.copy');tmp.write_bytes(p.read_bytes());os.replace(tmp,p)
        before=self.req('/api/resources');r=self.scan();s=self.req('/api/library-health');body={'scanJobId':s['jobId'],'sha256':r['duplicates'][0]['sha256']}
        self.req('/api/library-health/share','POST',body,headers={'Origin':'https://evil.example'},status=403)
        self.req('/api/library-health/share','POST',{'sha256':'bad'},status=400)
        self.req('/api/library-health/share','POST',body)
        for _ in range(200):
            job=self.req('/api/library-health')['sharing']
            if job['status']!='running':break
            time.sleep(.01)
        self.assertEqual(job['status'],'complete',job);self.assertEqual(self.req('/api/resources'),before)
        for aid in [x['id'],y['id']]:self.assertEqual(self.req('/api/files/'+aid),fixture.PNG)
        self.assertTrue(os.path.samefile(Path(self.temp.name)/'files'/x['id'],p))
        with zipfile.ZipFile(io.BytesIO(self.req('/api/backups/'+job['backup']['name']))) as z:self.assertEqual(z.read('files/'+y['id']),fixture.PNG)

if __name__=='__main__':unittest.main()
