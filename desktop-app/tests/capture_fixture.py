"""Test-only public-host routing to a local HTTP fixture. Never used by production."""
import json
import socket
import struct
import threading
import time
import zlib
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch


def png_bytes():
    def chunk(name, data):
        return struct.pack('>I', len(data))+name+data+struct.pack('>I', zlib.crc32(name+data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0))+chunk(b'IDAT', zlib.compress(b'\0\xff'))+chunk(b'IEND', b'')


class Fixture:
    def __init__(self):
        self.calls, self.lock = [], threading.Lock()
        fixture = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                with fixture.lock:
                    fixture.calls.append(self.path)
                code, mime, raw, headers = 200, 'text/html; charset=utf-8', b'', {}
                if self.path.startswith('/redirect-private'):
                    code, headers = 302, {'Location': 'http://127.0.0.1/private'}
                elif self.path.startswith('/redirect'):
                    code, headers = 302, {'Location': '/page'}
                elif self.path.startswith('/image'):
                    mime, raw = 'image/png', png_bytes()
                elif self.path.startswith('/invalid-image'):
                    mime, raw = 'image/png', b'\x89PNG\r\n\x1a\nnot-a-real-image'
                elif self.path.startswith('/wrong-type'):
                    mime, raw = 'text/html', png_bytes()
                elif self.path.startswith('/fail'):
                    code = 503
                elif self.path.startswith('/denied'):
                    code = 403
                elif self.path.startswith('/slow'):
                    time.sleep(.3)
                    raw = b'<title>Delayed</title>'
                elif self.path.startswith('/incomplete'):
                    raw = b'<html><p>No title or description</p></html>'
                else:
                    image = '/invalid-image' if self.path.startswith('/bad-cover') else '/image'
                    raw = ('<title>React Component Library</title><meta property="og:description" content="Useful React UI components"><meta property="og:image" content="'+image+'"><link rel="icon" href="/icon.png"><link rel="canonical" href="/canonical">').encode()
                self.send_response(code)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(raw)))
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                try:
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    @contextmanager
    def route(self, timeout=None):
        import capture
        real_dns, real_request, real_fetch = socket.getaddrinfo, capture._request, capture.public_fetch
        def dns(host, port, **kwargs):
            if str(host) == 'offline.fixture.invalid':
                raise socket.gaierror('Fixture DNS failure')
            if str(host).endswith('.fixture.invalid'):
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', port))]
            return real_dns(host, port, **kwargs)
        def request(target, method, limit, deadline):
            if target[1].endswith('.fixture.invalid'):
                # Keep the real request parser, response bounds and timer. Only the
                # test transport routes an already public-validated host to the fixture.
                return real_request((target[0], target[1], self.server.server_port, '127.0.0.1'), method, limit, deadline)
            raise AssertionError('Fixture must not contact the real Internet')
        def fetch(url, method='GET', limit=2*1024*1024, timeout=8):
            return real_fetch(url, method, limit, min(timeout, self.timeout) if self.timeout else timeout)
        self.timeout = timeout
        with patch('capture.socket.getaddrinfo', side_effect=dns), patch('capture._request', side_effect=request), patch('capture.public_fetch', side_effect=fetch):
            yield
