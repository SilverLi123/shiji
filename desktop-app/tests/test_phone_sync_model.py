"""Real native model HTTP-state and render-size QR regressions; disposable local server."""
import json,subprocess,tempfile,threading,time,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
class PhoneSyncPresentationTests(unittest.TestCase):
 def test_status_recovery_and_dense_qr(self):
  state={'enabled':False,'pairingAvailable':False,'addresses':['192.168.1.10'],'devices':[]}
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    raw=json.dumps(state).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
   def do_POST(self):
    self.rfile.read(int(self.headers.get('Content-Length','0')))
    # Action succeeds but its response is lost/bad, then a later status confirms it.
    state['enabled']=True;self.send_response(500);self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'{}')
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with tempfile.TemporaryDirectory(prefix='shiji-native-ui-state-') as folder:
    folder=Path(folder);source=folder/'main.swift';binary=folder/'PresentationTests'
    source.write_text('''import SwiftUI
import Vision
@main struct Tests {
 @MainActor static func main() async throws {
  let model=PhoneSyncModel(base:URL(string:CommandLine.arguments[1])!)
  await model.perform();precondition(!model.enabled && model.error==nil)
  await model.perform("enable");precondition(model.error != nil)
  await model.refresh();precondition(model.enabled && model.error==nil,"confirmed action should clear stale failure")
  model.code="shiji-sync://pair?"+String(repeating:"aB09+%2F",count:240)
  model.copied=true;model.expires=Date().addingTimeInterval(300)
  // Unconsumed status preserves code and copy feedback; consumed status clears both.
  model.update(["enabled":true,"pairingAvailable":true,"addresses":["192.168.1.10"],"devices":[]])
  precondition(model.copied && !model.code.isEmpty)
  guard let image=model.qr,let cg=image.cgImage(forProposedRect:nil,context:nil,hints:nil),let canvas=CGContext(data:nil,width:568,height:568,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)else{fatalError("QR unavailable")}
  canvas.setFillColor(NSColor.white.cgColor);canvas.fill(CGRect(x:0,y:0,width:568,height:568));canvas.interpolationQuality = .none;canvas.draw(cg,in:CGRect(x:24,y:24,width:520,height:520))
  let request=VNDetectBarcodesRequest();request.symbologies=[.qr];request.usesCPUOnly=true // Avoid optional ANE model availability in host CI; still decode the actual rendered QR.
  try VNImageRequestHandler(cgImage:canvas.makeImage()!).perform([request])
  precondition(request.results?.first?.payloadStringValue==model.code,"dense pairing QR must decode at shipped Retina size")
  model.update(["enabled":true,"pairingAvailable":false,"addresses":["192.168.1.10"],"devices":[]])
  precondition(model.code.isEmpty && model.expires==nil && !model.copied)
  print("PASS: native status recovery, code consumption and rendered QR decoding")
 }
}
''')
    subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5',str(ROOT/'desktop/PhoneSync.swift'),str(source),'-o',str(binary)],check=True,capture_output=True,text=True)
    result=subprocess.run([str(binary),'http://127.0.0.1:'+str(server.server_port)],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    self.assertIn('PASS:',result.stdout)
  finally:server.shutdown();server.server_close()
