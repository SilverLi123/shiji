"""Actual Swift/WebKit delegate and diagnostics contracts, temporary QA roots only."""
import os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NativeLifecycleTests(unittest.TestCase):
 def test_delegate_failure_teardown_and_bounded_private_log(self):
  with tempfile.TemporaryDirectory(prefix='shiji-native-lifecycle-') as folder:
   root=Path(folder);app=(ROOT/'desktop/App.swift').read_text().split('struct FunctionalGlass')[0]
   (root/'Runtime.swift').write_text(app)
   (root/'main.swift').write_text('''import AppKit
import WebKit
@main struct Tests {
 @MainActor static func main() throws {
  let runtime=LibraryRuntime(),delegate=ManagementView.Coordinator(runtime)
  let view=WKWebView();runtime.webView=view;view.navigationDelegate=delegate
  delegate.webView(view,didFailProvisionalNavigation:nil,withError:NSError(domain:NSURLErrorDomain,code:NSURLErrorCancelled))
  precondition(runtime.pageError==nil,"cancelled navigation is not a failure")
  delegate.webView(view,didFailProvisionalNavigation:nil,withError:NSError(domain:NSURLErrorDomain,code:NSURLErrorCannotConnectToHost))
  precondition(runtime.pageError != nil)
  delegate.webView(view,didFinish:nil);precondition(runtime.pageError==nil)
  delegate.webViewWebContentProcessDidTerminate(view);precondition(runtime.pageError != nil)
  ManagementView.dismantleNSView(view,coordinator:delegate)
  precondition(runtime.webView==nil && view.navigationDelegate==nil && view.uiDelegate==nil)
  let trace=runtime.diagnostics
  trace.record("test",["ok":true])
  let mode=try FileManager.default.attributesOfItem(atPath:trace.file.path)[.posixPermissions] as! NSNumber
  precondition(mode.intValue==0o600)
  try Data(repeating:32,count:1_048_600).write(to:trace.file)
  trace.record("rotated")
  precondition(FileManager.default.fileExists(atPath:trace.file.appendingPathExtension("previous").path))
  let bytes=try Data(contentsOf:trace.file);precondition(bytes.count<1024)
  print("PASS: native navigation cancellation/failure/termination, teardown and private bounded diagnostics")
 }
}
''')
   binary=root/'native-test'
   compiled=subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5',str(root/'Runtime.swift'),str(ROOT/'desktop/RuntimeDiagnostics.swift'),str(root/'main.swift'),'-o',str(binary)],capture_output=True,text=True)
   self.assertEqual(compiled.returncode,0,compiled.stderr)
   result=subprocess.run([str(binary)],env={**os.environ,'SHIJI_DATA_DIR':str(root/'data'),'SHIJI_PORT':'1'},capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn('PASS:',result.stdout)
