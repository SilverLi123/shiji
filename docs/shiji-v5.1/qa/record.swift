import Foundation
import AppKit
import ScreenCaptureKit
import AVFoundation
final class Recording: NSObject, SCRecordingOutputDelegate {
 func recordingOutputDidStartRecording(_ output:SCRecordingOutput){print("recording-start");fflush(stdout)}
 func recordingOutput(_ output:SCRecordingOutput,didFailWithError error:Error){print("recording-error \(error)")}
 func recordingOutputDidFinishRecording(_ output:SCRecordingOutput){print("recording-finished");fflush(stdout)}
}
@main struct Capture {
 static func main() async throws {
  _ = NSApplication.shared
  let pid=Int32(CommandLine.arguments[1])!,out=URL(fileURLWithPath:CommandLine.arguments[2]),seconds=UInt64(CommandLine.arguments[3])!
  let content=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:false)
  guard let window=content.windows.first(where:{$0.owningApplication?.processID==pid && $0.title=="拾集 · 开发资源库"}) else {throw NSError(domain:"QA-window-not-found",code:1)}
  let filter=SCContentFilter(desktopIndependentWindow:window),config=SCStreamConfiguration();config.width=1180;config.height=820;config.minimumFrameInterval=CMTime(value:1,timescale:30);config.showsCursor=false;config.capturesAudio=false
  let recordingConfig=SCRecordingOutputConfiguration();recordingConfig.outputURL=out;recordingConfig.videoCodecType = .h264;recordingConfig.outputFileType = .mp4
  let delegate=Recording(),recording=SCRecordingOutput(configuration:recordingConfig,delegate:delegate),stream=SCStream(filter:filter,configuration:config,delegate:nil)
  try stream.addRecordingOutput(recording);try await stream.startCapture();try await Task.sleep(nanoseconds:seconds*1_000_000_000);try await stream.stopCapture();try await Task.sleep(nanoseconds:500_000_000)
 }
}
