"""Owned desktop service. A locked library and pre-bound loopback socket prevent double starts."""
import argparse
import fcntl
import os
from pathlib import Path
import signal
import threading
from http.server import ThreadingHTTPServer
import server
from storage import Store
from sync_transport import SyncService

class DesktopHandler(server.Handler):
    def do_GET(self):
        if self.path == '/api/mobile-sync':
            if self.safe_request():self.send_json(200,self.server.mobile_sync.status())
            return
        if self.path == '/api/desktop-status':
            if self.safe_request(): self.send_json(200, {'app':'DevResourceLibrary','instance':self.server.instance,'pid':os.getpid()})
            return
        super().do_GET()
    def do_POST(self):
        if self.path.startswith('/api/mobile-sync/'):
            if not self.safe_request():return
            try:
                body=self.read_json();service=self.server.mobile_sync
                if self.path=='/api/mobile-sync/enable':result=service.start()
                elif self.path=='/api/mobile-sync/stop':service.stop();result=service.status()
                elif self.path=='/api/mobile-sync/pair':result=service.pairing(body.get('address'))
                elif self.path=='/api/mobile-sync/revoke':service.revoke();result=service.status()
                else:self.send_json(404,{'error':'同步操作不存在。'});return
                self.send_json(200,result)
            except (OSError,ValueError,RuntimeError):self.send_json(400,{'error':'同步操作失败。检查端口、电脑网络与磁盘后重试。'})
            return
        super().do_POST()

def run(data_dir, port, instance):
    root=Path(data_dir).expanduser().resolve();root.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (root/'.desktop.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('这个资源库已由另一个 App 打开。')
        # Bind first: a port collision must not open or migrate the database.
        http=ThreadingHTTPServer(('127.0.0.1',port),DesktopHandler);http.instance=instance
        store=None
        def stop(*_): threading.Thread(target=http.shutdown,daemon=True).start()
        previous={s:signal.signal(s,stop) for s in (signal.SIGINT,signal.SIGTERM)}
        try:
            store=Store(root);server.STORE=store;http.mobile_sync=SyncService(store,port=int(os.environ.get("SHIJI_SYNC_PORT","8784")));store.start_auto_backup();store.start_preview_worker()
            print('READY '+str(http.server_port),flush=True);http.serve_forever(poll_interval=.2)
        finally:
            if store:
                if hasattr(http,'mobile_sync'):http.mobile_sync.stop()
                store.stop_auto_backup();store.stop_preview_worker()
            http.server_close()
            for s,handler in previous.items():signal.signal(s,handler)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',required=True);parser.add_argument('--port',type=int,default=8782);parser.add_argument('--instance',required=True)
    args=parser.parse_args()
    try: run(args.data_dir,args.port,args.instance)
    except (OSError,RuntimeError) as error: raise SystemExit('无法启动本地资源库：'+str(error))
