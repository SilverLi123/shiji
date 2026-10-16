import sys,tempfile,threading,unittest,subprocess,shutil,time
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage import Store

class QueryUIIntegration(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Requires Node DOM test runtime')
    def test_actual_v5_scripts_use_paging_hydration_and_full_match_selection(self):
        self.run_page()

    @unittest.skipUnless(shutil.which('node'),'Requires Node DOM test runtime')
    def test_slow_capability_discovery_never_starts_legacy_full_library_poll(self):
        self.run_page('slow')

    @unittest.skipUnless(shutil.which('node'),'Requires Node DOM test runtime')
    def test_capability_guard_with_slow_initial_script_delivery(self):
        self.run_page('slow', delay_asset=True)

    def run_page(self, mode='normal', delay_asset=False):
        with tempfile.TemporaryDirectory() as data:
            store=Store(data)
            for i in range(130):store.save({'title':'needle' if i==0 else '资源 '+str(i),'kind':'code','snippet':'code\n'*500+'END-OF-FULL-CODE','notes':'notes'*500,'inbox':True})
            class Handler(server.Handler):
                def do_GET(self):
                    if delay_asset and self.path.split('?')[0]=='/app.js':time.sleep(3) # Deliberate fixture-only script delivery latency.
                    return super().do_GET()
            old=server.STORE;server.STORE=store;http=ThreadingHTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
            try:
                result=subprocess.run(['node',str(Path(__file__).with_name('query_ui_integration.cjs')),'http://127.0.0.1:'+str(http.server_port)+'/',mode],text=True,capture_output=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr[-5000:]);self.assertIn('"passed":true',result.stdout)
                self.assertEqual(sum(r['inbox'] for r in store.state()['resources']),0)
                self.assertTrue(next(r for r in store.state()['resources'] if r['title']=='Changed title')['snippet'].endswith('END-OF-FULL-CODE'))
            finally:http.shutdown();http.server_close();t.join();server.STORE=old

if __name__=='__main__':unittest.main()
