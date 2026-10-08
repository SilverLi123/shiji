import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
try:import capture
except ImportError:capture=None
class Capture(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(capture,'capture module is not implemented')
    def test_html_metadata_handles_entities_and_relative_images(self):
        r=capture.metadata_from_html('https://example.com/docs/page',b'<title>React &amp; Design</title><meta property="og:description" content="UI library"><meta property="og:image" content="../preview.png"><link rel="icon" href="/favicon.png">')
        self.assertEqual(r['title'],'React & Design');self.assertEqual(r['thumbnail'],'https://example.com/preview.png');self.assertEqual(r['favicon'],'https://example.com/favicon.png')
    def test_public_fetch_rejects_private_and_credential_urls(self):
        for url in ['http://127.0.0.1/','http://169.254.169.254/','http://[::1]/','http://192.168.1.5/','https://user:pass@example.com/','http://8.8.8.8:8080/']:
            with self.subTest(url=url),self.assertRaises(ValueError):capture.resolve_public(url)
    def test_redirect_target_is_revalidated(self):
        with patch.object(capture,'_request',return_value=(302,{'location':'http://127.0.0.1/'},b'')),patch.object(capture,'resolve_public',side_effect=[('https://example.com/','example.com',443,'93.184.216.34'),ValueError('private')]):
            with self.assertRaises(ValueError):capture.public_fetch('https://example.com/')
    def test_access_denied_is_unknown_not_broken(self):
        self.assertEqual(capture.classify_status(403),'unknown');self.assertEqual(capture.classify_status(429),'unknown');self.assertEqual(capture.classify_status(404),'broken');self.assertEqual(capture.classify_status(200),'ok')
    def test_malicious_metadata_cannot_point_to_localhost(self):
        r=capture.metadata_from_html('https://example.com/',b'<meta property="og:image" content="http://127.0.0.1/a.png"><link rel="icon" href="javascript:alert(1)">')
        self.assertEqual(r['thumbnail'],'');self.assertEqual(r['favicon'],'')
