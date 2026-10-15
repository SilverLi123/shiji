"""Separate Node workers and real desktop HTTP; no browser-install claim."""
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import server
from storage import Store
from capture_fixture import png_bytes


@unittest.skipUnless(shutil.which('node'), 'Node needed for cross-process extension integration')
class ExtensionDelivery(unittest.TestCase):
    def test_offline_restart_lost_response_and_reconcile_after_trash(self):
        previous = server.STORE
        with tempfile.TemporaryDirectory(prefix='shiji-extension-delivery-') as directory:
            root = Path(directory)
            store = Store(root/'library')
            reserved = socket.socket()
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
            config = root/'config.json'
            config.write_text(json.dumps({'base': 'http://127.0.0.1:'+str(port), 'token': store.token()}))
            config.chmod(0o600)
            (root/'payload.json').write_text(json.dumps({'url': 'https://example.com/extension-qa',
                'title': 'Frozen screenshot', 'selection': 'Original selection',
                'screenshot': 'data:image/png;base64,'+base64.b64encode(png_bytes()).decode()}))
            def run(mode):
                result = subprocess.run(['node', str(Path(__file__).with_name('extension_delivery.cjs')), str(root), mode], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            try:
                run('offline')
            finally:
                reserved.close()
            self.assertEqual(store.state()['resources'], [])
            server.STORE = store
            http = ThreadingHTTPServer(('127.0.0.1', port), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            try:
                run('deliver-lost')
                resource = store.state()['resources'][0]
                self.assertEqual(len(resource['attachments']), 1)
                self.assertEqual(store.capture_status()['total'], 1)
                store.save({'title': 'Edited after lost reply', 'notes': 'Keep this'}, resource['id'])
                store.remove(resource['id'])
                before = store.get(resource['id'])
                # Reopen the actual SQLite Store as a backend restart would.
                store = Store(root/'library')
                server.STORE = store
                run('confirm')
                self.assertEqual(store.get(resource['id']), before)
                self.assertEqual(store.state()['resources'], [])
                self.assertEqual(store.capture_status()['total'], 1)
                self.assertEqual(len(list(store.files.iterdir())), 1)
            finally:
                http.shutdown()
                http.server_close()
                thread.join(2)
                server.STORE = previous
