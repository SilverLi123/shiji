"""Physical reuse must preserve logical identity, provenance and recovery."""
import errno
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import test_upgrade as fixture
sys.path.insert(0,str(fixture.APP))
from storage import Store

class Reuse(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def resource(self,title='resource'):
        return self.store.save({'kind':'file','title':title})['resource']
    def add(self,resource=None,raw=fixture.PNG,**metadata):
        resource=resource or self.resource()
        return self.store.attachment(resource['id'],raw,{'name':'a.png',**metadata})['attachment']
    def path(self,a):return self.store.files/a['id']
    def same_inode(self,a,b):return os.path.samefile(self.path(a),self.path(b))
    def scan(self):self.store._run_health();return self.store.health_status()['report']
    def failed_commit(self):
        original=self.store.connect
        class Connection:
            def __enter__(self):self.c=original();return self.c
            def __exit__(self,*args):self.c.rollback();self.c.close();raise sqlite3.OperationalError('commit failed')
        return patch.object(self.store,'connect',Connection)
    def test_distinct_metadata_and_resources_share_only_bytes(self):
        r=self.resource('first');a=self.add(r,author='author-a',license='需署名',sourceUrl='https://a.example/',cover=True)
        b=self.add(r,name='second.png',author='author-b',license='仅个人使用',sourceUrl='https://b.example/')
        c=self.add(author='third')
        self.assertNotEqual(a['id'],b['id']);self.assertNotEqual(a['resourceId'],c['resourceId'])
        self.assertTrue(self.same_inode(a,b));self.assertTrue(self.same_inode(a,c))
        self.store.update_attachment(b['id'],{'author':'edited','license':'待确认'})
        first=self.store.get(r['id']);self.assertEqual(first['attachments'][0]['author'],'author-a');self.assertEqual(first['coverId'],a['id'])
        report=self.scan();self.assertEqual(report['storedBytes'],3*len(fixture.PNG));self.assertEqual(report['uniqueStoredBytes'],len(fixture.PNG));self.assertEqual(report['sharedBytes'],2*len(fixture.PNG));self.assertEqual(report['sharedFiles'],2)
        self.assertEqual(len(report['duplicates'][0]['items']),3)
    def test_asset_copy_policy_and_trash_reuse_keep_independent_records(self):
        a=self.add();self.store.remove(a['resourceId'])
        saved=self.store.import_asset(fixture.PNG,{'requestId':'copy','name':'renamed.png','duplicatePolicy':'copy','author':'different'})['resource']
        b=saved['attachments'][0];self.assertTrue(self.same_inode(a,b));self.assertNotEqual(a['resourceId'],b['resourceId'])
        self.store.remove(a['resourceId'],restore=True);self.assertEqual(self.store.file(b['id'])[1].read_bytes(),fixture.PNG)
        self.assertEqual(self.store.get(a['resourceId'])['attachments'][0]['author'],'')
    def test_missing_corrupt_symlink_and_unreadable_candidates_are_not_shared(self):
        for problem in ['missing','corrupt','symlink','unreadable']:
            with self.subTest(problem=problem),tempfile.TemporaryDirectory() as directory:
                store=Store(directory);r=store.save({'kind':'file','title':'first'})['resource'];a=store.attachment(r['id'],fixture.PNG,{'name':'a.png'})['attachment'];source=store.files/a['id']
                if problem=='missing':source.unlink()
                elif problem=='corrupt':source.write_bytes(b'broken')
                elif problem=='symlink':source.unlink();outside=Path(directory)/'outside';outside.write_bytes(fixture.PNG);source.symlink_to(outside)
                target=store.save({'kind':'file','title':'second'})['resource']
                original=Path.open
                def readable(path,*args,**kwargs):
                    if path==source:raise PermissionError('unreadable')
                    return original(path,*args,**kwargs)
                with (patch.object(Path,'open',readable) if problem=='unreadable' else patch('file_store.os.link',wraps=os.link)):
                    b=store.attachment(target['id'],fixture.PNG,{'name':'b.png'})['attachment']
                dest=store.files/b['id'];self.assertFalse(dest.is_symlink());self.assertEqual(dest.read_bytes(),fixture.PNG)
                if source.exists() and not source.is_symlink():self.assertFalse(os.path.samefile(source,dest))
    def test_link_unavailable_falls_back_without_changing_source(self):
        a=self.add();r=self.resource('second')
        with patch('file_store.os.link',side_effect=OSError(errno.EXDEV,'unsupported')):b=self.add(r)
        self.assertFalse(self.same_inode(a,b));self.assertEqual(self.path(b).read_bytes(),fixture.PNG);self.assertEqual(self.scan()['sharedBytes'],0)
    def test_distinct_bytes_and_concurrent_identical_uploads(self):
        from concurrent.futures import ThreadPoolExecutor
        a=self.add();b=self.add(raw=fixture.PNG[:-1]+b'x');self.assertFalse(self.same_inode(a,b))
        resources=[self.resource(str(i)) for i in range(4)]
        with ThreadPoolExecutor(max_workers=4) as pool:copies=list(pool.map(self.add,resources))
        self.assertTrue(all(self.same_inode(a,item) for item in copies));self.assertEqual(len(self.store.state()['resources']),6)
    def test_publish_failure_removes_link_and_keeps_original(self):
        a=self.add();r=self.resource('second');before=self.store.state();paths=set(self.store.files.iterdir())
        with patch('file_store.os.replace',side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):self.add(r)
        self.assertEqual(self.store.state(),before);self.assertEqual(set(self.store.files.iterdir()),paths);self.assertEqual(self.path(a).stat().st_nlink,1)
    def test_existing_temp_conflict_is_preserved_on_failed_asset_import(self):
        aid='00000000-0000-4000-8000-000000000001';temporary=self.store.files/(aid+'.tmp');temporary.write_bytes(b'preexisting bytes');before=self.store.state()
        with patch('asset_import.uuid.uuid4',return_value=aid):
            with self.assertRaises(ValueError):self.store.import_asset(fixture.PNG,{'requestId':'conflict','name':'a.png','duplicatePolicy':'copy'})
        self.assertEqual(temporary.read_bytes(),b'preexisting bytes');self.assertEqual(self.store.state(),before)
    def test_candidate_change_to_symlink_is_rechecked_after_link(self):
        a=self.add();source=self.path(a);outside=Path(self.temp.name)/'outside';outside.write_bytes(b'private bytes');original=os.link
        def switched(src,dst,**kwargs):
            source.unlink();source.symlink_to(outside);return original(src,dst,**kwargs)
        with patch('file_store.os.link',switched):b=self.add()
        self.assertFalse(self.path(b).is_symlink());self.assertEqual(self.path(b).read_bytes(),fixture.PNG);self.assertEqual(outside.read_bytes(),b'private bytes')
    def test_attachment_and_asset_commit_failures_unlink_only_new_paths(self):
        a=self.add();r=self.resource('second');self.store.dirty=False;before=self.store.state();paths=set(self.store.files.iterdir())
        for operation in ['attachment','asset']:
            with self.subTest(operation=operation),self.failed_commit():
                with self.assertRaises(sqlite3.Error):
                    if operation=='attachment':self.add(r)
                    else:self.store.import_asset(fixture.PNG,{'requestId':'failed','name':'copy.png','duplicatePolicy':'copy'})
            self.assertEqual(self.store.state(),before);self.assertEqual(set(self.store.files.iterdir()),paths);self.assertEqual(self.path(a).read_bytes(),fixture.PNG);self.assertEqual(self.path(a).stat().st_nlink,1);self.assertFalse(self.store.dirty)
    def test_backup_keeps_all_ids_and_restore_reuses_verified_bytes(self):
        a=self.add(author='first');b=self.add(author='second');blob=self.store.backup_bytes()
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            self.assertEqual(archive.read('files/'+a['id']),fixture.PNG);self.assertEqual(archive.read('files/'+b['id']),fixture.PNG)
        with tempfile.TemporaryDirectory() as directory:
            restored=Store(directory);restored.restore_zip(blob)
            self.assertTrue(os.path.samefile(restored.files/a['id'],restored.files/b['id']))
            self.assertEqual(restored.get(a['resourceId'])['attachments'][0],a);self.assertEqual(restored.get(b['resourceId'])['attachments'][0],b)
    def test_repair_detaches_one_path_and_does_not_modify_its_peer(self):
        a=self.add();old=self.store.backup_bytes();b=self.add();self.assertTrue(self.same_inode(a,b))
        self.path(a).write_bytes(b'corrupted shared bytes');self.assertEqual(self.path(b).read_bytes(),b'corrupted shared bytes')
        result=self.store.restore_zip(old);self.assertEqual(result['repairedFiles'],1)
        self.assertEqual(self.path(a).read_bytes(),fixture.PNG);self.assertEqual(self.path(b).read_bytes(),b'corrupted shared bytes');self.assertFalse(self.same_inode(a,b))
    def test_restore_commit_failure_restores_original_shared_paths(self):
        a=self.add();b=self.add();blob=self.store.backup_bytes();self.path(a).write_bytes(b'old shared damage');before=self.store.state()
        original=self.store.connect;calls=0
        class Connection:
            def __enter__(self):self.c=original();return self.c
            def __exit__(self,*args):self.c.rollback();self.c.close();raise sqlite3.OperationalError('commit failed')
        def connections():
            nonlocal calls
            calls+=1;return original() if calls==1 else Connection()
        with patch.object(self.store,'connect',connections),self.assertRaises(sqlite3.Error):self.store.restore_zip(blob)
        self.assertEqual(self.store.state(),before);self.assertEqual(self.path(a).read_bytes(),b'old shared damage');self.assertEqual(self.path(b).read_bytes(),b'old shared damage');self.assertTrue(self.same_inode(a,b))

if __name__=='__main__':unittest.main()
