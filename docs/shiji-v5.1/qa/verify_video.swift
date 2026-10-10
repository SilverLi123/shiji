import Foundation
import AppKit
import AVFoundation
@main struct VerifyVideo {
 static func main() async throws {
  let url=URL(fileURLWithPath:CommandLine.arguments[1]),asset=AVURLAsset(url:url)
  let duration=try await asset.load(.duration),tracks=try await asset.loadTracks(withMediaType:.video)
  guard let track=tracks.first else {throw NSError(domain:"no-video-track",code:1)}
  let rate=try await track.load(.nominalFrameRate),size=try await track.load(.naturalSize)
  let generator=AVAssetImageGenerator(asset:asset);generator.appliesPreferredTrackTransform=true
  for seconds in [0.0,8.0,16.0,24.0] {
   let result=try await generator.image(at:CMTime(seconds:seconds,preferredTimescale:600))
   let png=NSBitmapImageRep(cgImage:result.image).representation(using:.png,properties:[:])!
   try png.write(to:URL(fileURLWithPath:CommandLine.arguments[2]+"-\(Int(seconds)).png"))
  }
  print("{\"durationSeconds\":\(CMTimeGetSeconds(duration)),\"width\":\(size.width),\"height\":\(size.height),\"nominalFrameRate\":\(rate),\"decodedFramesAtSeconds\":[0,8,16,24]}")
 }
}
