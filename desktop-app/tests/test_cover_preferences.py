import base64
import json
import sqlite3
import struct
import tempfile
import threading
import unittest
import zlib
from unittest.mock import patch
from storage import Store
from edits import EditConflict


def image_bytes():
    def chunk(name, body):
        return struct.pack('>I',len(body))+name+body+struct.pack('>I',zlib.crc32(name+body)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\x23\xa2\xe8\xff'))+chunk(b'IEND',b'')


class CoverPreferences(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
        self.r=self.store.save({'kind':'file','title':'Original title','notes':'Keep notes','tags':['New, exact'],'category':'灵感'})['resource']
    def tearDown(self):self.temp.cleanup()
    def body(self,r=None,config=None,cover=None,upload=None):
        r=r or self.r
        body={'config':config,'coverId':r['coverId'] if cover is None else cover,'expected':{'coverConfig':r.get('coverConfig'),'coverId':r['coverId']}}
        if upload is not None:body['upload']=upload
        return body
    def upload(self,name='actual.png'):
        return {'name':name,'mime':'image/png','base64':base64.b64encode(image_bytes()).decode()}
    def test_preferences_persist_restart_legacy_edit_reset_and_do_not_rename_resource(self):
        r=self.store.update_cover(self.r['id'],self.body(config={'style':'editorial','customTitle':'Cover only','extension':{'a':True}}))['resource']
        self.assertEqual(r['title'],'Original title');self.assertEqual(r['notes'],'Keep notes')
        self.assertEqual(Store(self.temp.name).get(r['id']),r)
        self.assertEqual(self.store.save({'title':'Edited source'},r['id'])['resource']['coverConfig'],r['coverConfig'])
        changed=self.store.update_cover(r['id'],self.body(r,config=None))['resource']
        self.assertIsNone(changed['coverConfig']);self.assertEqual(changed['title'],'Edited source')
        with self.store.connect() as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
    def test_idempotent_retry_and_stale_field_conflict_preserve_other_edits(self):
        body=self.body(config={'style':'developer'})
        self.store.save({'notes':'New note','favorite':True},self.r['id'])
        first=self.store.update_cover(self.r['id'],body)['resource'];self.store.dirty=False
        self.assertFalse(self.store.update_cover(self.r['id'],body)['changed']);self.assertFalse(self.store.dirty)
        self.assertEqual(first['notes'],'New note');self.assertTrue(first['favorite'])
        with self.assertRaises(EditConflict):self.store.update_cover(self.r['id'],self.body(config={'style':'minimal'}))
        self.assertEqual(self.store.get(self.r['id']),first)
    def test_upload_deduplicates_bytes_even_renamed_and_idempotent_uncertain_retry(self):
        body=self.body(config={'style':'spatial','imageSource':'image'},upload=self.upload())
        first=self.store.update_cover(self.r['id'],body)['resource'];aid=first['coverId']
        self.assertEqual(len(first['attachments']),1);self.assertEqual((self.store.files/aid).read_bytes(),image_bytes())
        self.assertFalse(self.store.update_cover(self.r['id'],body)['changed'])
        other=self.store.update_cover(self.r['id'],self.body(first,config={'style':'minimal'},upload=self.upload('renamed.png')))['resource']
        self.assertEqual(other['coverId'],aid);self.assertEqual(len(other['attachments']),1)
    def test_foreign_nonimage_corrupt_oversized_and_stale_uploads_leave_no_files(self):
        other=self.store.save({'kind':'file','title':'Other'})['resource']
        a=self.store.attachment(other['id'],image_bytes(),{'name':'other'})['attachment']
        b=self.store.attachment(self.r['id'],b'text',{'name':'text'})['attachment']
        before=self.store.state();files=set(self.store.files.iterdir())
        for body in [self.body(cover=a['id']),self.body(cover=b['id']),self.body(upload={**self.upload(),'base64':'!'}),self.body(upload={**self.upload(),'mime':'image/jpeg'}),self.body(upload={**self.upload(),'base64':base64.b64encode(b'broken').decode()}),self.body(upload={**self.upload(),'base64':'A'*(7*1024*1024)}),self.body(config={'primary':'red'})]:
            with self.assertRaises(ValueError):self.store.update_cover(self.r['id'],body)
            self.assertEqual(self.store.state(),before);self.assertEqual(set(self.store.files.iterdir()),files)
        self.store.update_cover(self.r['id'],self.body(config={'style':'minimal'}))
        with self.assertRaises(EditConflict):self.store.update_cover(self.r['id'],self.body(config={'style':'developer'},upload=self.upload()))
        self.assertEqual(set(self.store.files.iterdir()),files)
    def test_concurrent_choices_do_not_overwrite_or_publish_losing_upload(self):
        barrier=threading.Barrier(3);results=[]
        def writer(style):
            barrier.wait()
            try:self.store.update_cover(self.r['id'],self.body(config={'style':style},upload=self.upload()));results.append('saved')
            except EditConflict:results.append('conflict')
        workers=[threading.Thread(target=writer,args=(style,)) for style in ('editorial','spatial')]
        for worker in workers:worker.start()
        barrier.wait()
        for worker in workers:worker.join(3);self.assertFalse(worker.is_alive())
        self.assertCountEqual(results,['saved','conflict'])
        current=self.store.get(self.r['id']);self.assertEqual(len(current['attachments']),1);self.assertEqual(len(list(self.store.files.iterdir())),1)

    def test_write_failure_rolls_back_preferences_attachment_and_published_bytes(self):
        before=self.store.state();self.store.dirty=False
        with patch.object(self.store,'_projects',side_effect=sqlite3.OperationalError('QA rollback')):
            with self.assertRaises(sqlite3.OperationalError):self.store.update_cover(self.r['id'],self.body(config={'style':'editorial'},upload=self.upload()))
        self.assertEqual(self.store.state(),before);self.assertEqual(list(self.store.files.iterdir()),[]);self.assertFalse(self.store.dirty)
    def test_future_data_roundtrips_readonly_until_explicit_reset_and_guarded_edits(self):
        future={'version':3,'style':'unknown','next':{'choice':'retained'}}
        r=self.store.save({'coverConfig':future},self.r['id'])['resource']
        self.assertEqual(Store(self.temp.name).get(r['id'])['coverConfig'],future)
        self.assertEqual(self.store.edit_resource(r['id'],{'changes':{'title':'Source edit'},'expected':{'title':r['title']}})['resource']['coverConfig'],future)
        with self.assertRaises(ValueError):self.store.update_cover(r['id'],self.body(r,config={'style':'editorial'}))
        self.assertIsNone(self.store.update_cover(r['id'],self.body(r,config=None))['resource']['coverConfig'])
        r=self.store.get(r['id']);result=self.store.edit_resource(r['id'],{'changes':{'coverConfig':{'style':'minimal'}},'expected':{'coverConfig':None}})['resource'];self.assertEqual(result['coverConfig']['style'],'minimal')
    def test_zip_remaps_existing_cover_reference_json_fallback_and_old_backups(self):
        source=self.store.update_cover(self.r['id'],self.body(config={'style':'spatial','customTitle':'封面','imageSource':'image'},upload=self.upload()))['resource'];blob=self.store.backup_bytes()
        with tempfile.TemporaryDirectory() as d:
            target=Store(d);foreign=target.save({'title':'Collision','kind':'file'})['resource'];a=target.attachment(foreign['id'],image_bytes(),{'name':'foreign'})['attachment']
            # Establish a valid conflicting attachment ID owned by a different resource.
            with target.connect() as c:
                c.execute('UPDATE attachments SET id=?,payload=? WHERE id=?',(source['coverId'],json.dumps({**a,'id':source['coverId']}),a['id']))
            (target.files/a['id']).rename(target.files/source['coverId'])
            target.restore_zip(blob);restored=target.get(source['id'])
            self.assertNotEqual(restored['coverId'],source['coverId']);self.assertEqual(restored['coverConfig'],source['coverConfig'])
            self.assertEqual(target.file(restored['coverId'])[1].read_bytes(),image_bytes())
        with tempfile.TemporaryDirectory() as d:
            target=Store(d);target.import_json(self.store.export());r=target.state()['resources'][0]
            self.assertEqual(r['coverId'],'');self.assertEqual(r['coverConfig'],source['coverConfig'])
        old=self.store.save({'kind':'file','title':'Old format'})['resource'];self.assertNotIn('coverConfig',old)
        with tempfile.TemporaryDirectory() as d:
            target=Store(d);target.restore_zip(self.store.backup_bytes());self.assertNotIn('coverConfig',target.get(old['id']))
    def test_late_capture_does_not_override_cover_preferences_or_manual_image(self):
        r=self.store.save({'url':'https://example.test/capture','title':'example.test'})['resource']
        entered,release=threading.Event(),threading.Event()
        def fetch(*args):entered.set();release.wait(3);return {'metadata':{'title':'Late title','thumbnail':'https://example.test/image.png'}}
        try:
            with patch('capture_jobs.fetch_payload',side_effect=fetch):
                t=threading.Thread(target=self.store.capture_step);t.start();self.assertTrue(entered.wait(2))
                chosen=self.store.update_cover(r['id'],self.body(r,config={'imageSource':'poster','customTitle':'手工封面'},upload=self.upload()))['resource'];release.set();t.join(3);self.assertFalse(t.is_alive())
            self.assertEqual(self.store.get(r['id']),chosen)
        finally:release.set()

if __name__=='__main__':unittest.main()
