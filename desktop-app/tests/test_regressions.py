import io
import json
import socket
import threading
import time
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store, Duplicate
import capture

PNG=b'\x89PNG\r\n\x1a\nfixture'
class Regressions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def add(self,**extra):return self.store.save({'url':'https://example.com/','title':'A',**extra})['resource']
    def test_backup_rejects_script_resource_and_smart_ids_without_mutation(self):
        self.add();blob=self.store.backup_bytes()
        for section in ('resources','smartCollections'):
            out=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(blob)) as src,zipfile.ZipFile(out,'w') as dst:
                m=json.loads(src.read('manifest.json'))
                evil='"><img src=x onerror=alert(1)>'
                if section=='resources':m['resources'][0]['id']=evil
                else:m['smartCollections']=[{'id':evil,'name':'unsafe','filters':{}}]
                for name in src.namelist():dst.writestr(name,json.dumps(m) if name=='manifest.json' else src.read(name))
            with self.assertRaises(ValueError):self.store.restore_zip(out.getvalue())
            self.assertEqual(len(self.store.state()['resources']),1)
    def test_valid_backup_repairs_missing_file_and_startup_remains_available(self):
        r=self.add();a=self.store.attachment(r['id'],PNG,{'name':'cover.png','cover':True})['attachment'];blob=self.store.backup_bytes()
        (self.store.files/a['id']).unlink()
        self.store.start_auto_backup()
        import time
        deadline=time.monotonic()+3
        while not self.store.backup_list().get('warning') and time.monotonic()<deadline:time.sleep(.01)
        self.store.stop_auto_backup()
        self.assertTrue(self.store.backup_list().get('warning'))
        self.store.restore_zip(blob)
        self.assertEqual(self.store.file(a['id'])[1].read_bytes(),PNG)
        self.assertEqual(self.store.get(r['id'])['coverId'],a['id'])
    def test_edit_cannot_overwrite_deleted_duplicate(self):
        a=self.add();b=self.add(url='https://b.example/',notes='B note',projects=['B project'])
        self.store.remove(b['id'])
        with self.assertRaises(Duplicate):self.store.save({**a,'url':b['url'],'title':'Edited A'},a['id'])
        self.assertEqual(self.store.get(a['id'])['title'],'A');self.assertEqual(self.store.get(b['id'])['notes'],'B note');self.assertTrue(self.store.get(b['id'])['deleted'])
    def test_json_import_preserves_smart_filters(self):
        self.store.smart({'name':'React','filters':{'tags':['React']}});data=self.store.export()
        with tempfile.TemporaryDirectory() as dst:
            other=Store(dst);other.import_json(data)
            self.assertEqual(other.state()['smartCollections'][0]['filters']['tags'],['React'])
    def test_fetch_deadline_bounds_slow_body(self):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();port=listener.getsockname()[1]
        def serve():
            try:
                conn,_=listener.accept()
                with conn:
                    conn.recv(4096);conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 8\r\n\r\n')
                    for _ in range(8):time.sleep(.07);conn.sendall(b'x')
            except OSError:pass
            finally:listener.close()
        threading.Thread(target=serve,daemon=True).start();begin=time.monotonic()
        with patch.object(capture,'resolve_public',return_value=('http://example.com/','example.com',port,'127.0.0.1')):
            with self.assertRaises((TimeoutError,OSError)):capture.public_fetch('http://example.com/',timeout=.2)
        self.assertLess(time.monotonic()-begin,.45)
    def test_fetch_deadline_bounds_dns(self):
        def slow(url):time.sleep(.6);return ('http://example.com/','example.com',80,'93.184.216.34')
        begin=time.monotonic()
        with patch.object(capture,'resolve_public',side_effect=slow):
            with self.assertRaises(TimeoutError):capture.public_fetch('http://example.com/',timeout=.1)
        self.assertLess(time.monotonic()-begin,.4)
