import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_upgrade as fixture

class Assets(unittest.TestCase):
    setUp=fixture.Integration.setUp
    start=fixture.Integration.start
    tearDown=fixture.Integration.tearDown
    req=fixture.Integration.req
    def preview(self,raw=fixture.PNG,**extra):
        return self.req('/api/assets/preview','POST',{'files':[{'name':'图片.png','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),**extra}]})
    def upload(self,raw=fixture.PNG,status=200,**extra):
        meta={'requestId':'request-1','name':'图片.png','title':'素材','sha256':hashlib.sha256(raw).hexdigest(),**extra}
        h={'X-Metadata':base64.b64encode(json.dumps(meta,ensure_ascii=False).encode()).decode()}
        data=self.req('/api/assets/import','POST',raw=raw,headers=h,status=status)
        return json.loads(data)
    def test_atomic_content_type_provenance_and_retry_restart(self):
        self.req('/api/collections','POST',{'name':'项目','autoTags':['自动']})
        before=self.req('/api/resources');plan=self.preview();self.assertEqual(plan['items'][0]['status'],'new');self.assertEqual(self.req('/api/resources'),before)
        metadata={'tags':['原标签'],'projects':['项目'],'sourceUrl':'https://source.example/','licenseUrl':'https://source.example/license','license':'需署名','author':'作者','colors':['#123456'],'path':'素材包/贴图/图片.png'}
        result=self.upload(**metadata);r=result['resource'];a=r['attachments'][0]
        self.assertEqual(a['resourceId'],r['id']);self.assertEqual(r['coverId'],a['id']);self.assertEqual(r['category'],'美术素材');self.assertIn('自动',r['tags'])
        for k in ['sourceUrl','licenseUrl','license','author']:self.assertEqual(a[k],metadata[k]);self.assertEqual(r[k],metadata[k])
        self.assertEqual(r['notes'],'原文件夹路径：素材包/贴图/图片.png');self.assertEqual(self.req('/api/files/'+a['id']),fixture.PNG)
        repeated=self.upload(**metadata);self.assertTrue(repeated['replayed']);self.assertEqual(repeated['resource']['id'],r['id'])
        self.proc.terminate();self.proc.wait();self.proc.stdout.close();self.proc.stderr.close();self.start()
        self.assertEqual(self.upload(**metadata)['resource']['id'],r['id']);self.assertEqual(len(self.req('/api/resources')['resources']),1)
        self.upload(title='changed',status=400,**metadata);self.assertEqual(len(self.req('/api/resources')['resources']),1)
    def test_duplicates_skip_copy_trash_and_batch(self):
        r=self.upload()['resource'];before=self.req('/api/resources')
        self.assertEqual(self.preview()['items'][0]['status'],'existing')
        self.assertEqual(self.upload(requestId='skip')['status'],'skipped');self.assertEqual(self.req('/api/resources'),before)
        copied=self.upload(requestId='copy',duplicatePolicy='copy')['resource'];self.assertNotEqual(copied['id'],r['id'])
        self.assertEqual(self.upload(requestId='copy',duplicatePolicy='copy')['resource']['id'],copied['id'])
        self.req('/api/resources/'+r['id'],'DELETE');self.req('/api/resources/'+copied['id'],'DELETE')
        self.assertEqual(self.preview()['items'][0]['status'],'trash');self.assertTrue(self.upload(requestId='trashskip')['deleted'])
        raw=b'other content';d=hashlib.sha256(raw).hexdigest()
        plan=self.req('/api/assets/preview','POST',{'files':[{'name':'a.bin','size':len(raw),'sha256':d},{'name':'b.bin','size':len(raw),'sha256':d}]})
        self.assertEqual([x['status'] for x in plan['items']],['new','duplicate'])
    def test_bad_existing_bytes_missing_and_symlink_are_not_duplicates(self):
        row=self.upload()['resource'];path=Path(self.temp.name)/'files'/row['attachments'][0]['id']
        path.write_bytes(b'corrupt');self.assertEqual(self.preview()['items'][0]['status'],'new')
        path.unlink();self.assertEqual(self.preview()['items'][0]['status'],'new')
        outside=Path(self.temp.name)/'outside';outside.write_bytes(fixture.PNG);path.symlink_to(outside)
        self.assertEqual(self.preview()['items'][0]['status'],'new');self.assertEqual(self.upload(requestId='intact-new')['status'],'saved')
    def test_validation_never_creates_resource_or_file(self):
        before=self.req('/api/resources')
        for bad in [{'title':''},{'license':'商用无忧'},{'path':'../secret'},{'path':'/absolute/path'},{'sha256':'wrong'},{'projects':['missing']},{'duplicatePolicy':'overwrite'},{'requestId':'/outside'}]:
            self.upload(status=400,**bad)
            self.assertEqual(self.req('/api/resources'),before);self.assertEqual(list((Path(self.temp.name)/'files').iterdir()),[])
        self.req('/api/assets/validate','POST',{'sourceUrl':'javascript:evil'},status=400)
        self.req('/api/assets/preview','POST',{'files':[]},status=400)
        self.req('/api/assets/preview','POST',{'files':[{}]*201},status=400)
        self.assertEqual(self.preview(size=0)['items'][0]['status'],'invalid')
        self.assertEqual(self.preview(size=64*1024*1024+1)['items'][0]['status'],'invalid')
        self.assertEqual(self.preview(path='a/../b')['items'][0]['status'],'invalid')
        self.assertEqual(self.req('/api/resources'),before)
    def test_audio_and_unknown_content_not_inferred_from_extension(self):
        r=self.upload(raw=b'RIFF'+b'\x00'*4+b'WAVE'+b'x'*20,name='audio.png')['resource'];self.assertEqual(r['category'],'音频');self.assertEqual(r['coverId'],'');self.assertEqual(r['attachments'][0]['mime'],'audio/wav')
        r=self.upload(raw=b'not an image',name='pretend.png',requestId='unknown')['resource'];self.assertEqual(r['category'],'其他');self.assertEqual(r['coverId'],'')
    def test_full_backup_roundtrip_bytes_and_folders(self):
        r=self.upload(path='包/声音.png')['resource'];backup=self.req('/api/backup.zip')
        import sys
        sys.path.insert(0,str(fixture.APP));from storage import Store
        with tempfile.TemporaryDirectory() as d:
            other=Store(d);other.restore_zip(backup);saved=other.state()['resources'][0]
            self.assertEqual(saved['notes'],r['notes']);self.assertEqual(saved['attachments'],r['attachments']);self.assertEqual(other.file(saved['coverId'])[1].read_bytes(),fixture.PNG)

class AtomicDisk(unittest.TestCase):
    def test_disk_and_commit_failure_remove_files_and_roll_back(self):
        import sys,sqlite3
        sys.path.insert(0,str(fixture.APP));from storage import Store
        for fail in ['write','commit']:
            with tempfile.TemporaryDirectory() as d:
                store=Store(d);before=store.state();original=store.connect
                class Connection:
                    def __init__(self):self.c=original()
                    def __enter__(self):return self.c
                    def __exit__(self,*args):self.c.rollback();self.c.close();raise sqlite3.OperationalError('simulated commit failure')
                kwargs={'requestId':'disk-test','name':'a.png'}
                with (patch.object(Path,'write_bytes',side_effect=OSError('disk full')) if fail=='write' else patch.object(store,'connect',Connection)):
                    with self.assertRaises((OSError,sqlite3.Error)):store.import_asset(fixture.PNG,kwargs)
                self.assertEqual(store.state(),before);self.assertEqual(list(store.files.iterdir()),[]);self.assertFalse(store.dirty)
