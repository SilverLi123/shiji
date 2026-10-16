// Extract an unedited frame from the recorded QA window, for the report.
import AppKit
import AVFoundation
let args=CommandLine.arguments
guard args.count==4,let seconds=Double(args[2]) else { fatalError("video seconds output.png") }
let asset=AVURLAsset(url:URL(fileURLWithPath:args[1]))
let generator=AVAssetImageGenerator(asset:asset)
generator.appliesPreferredTrackTransform=true
let image=try generator.copyCGImage(at:CMTime(seconds:seconds,preferredTimescale:600),actualTime:nil)
let representation=NSBitmapImageRep(cgImage:image)
try representation.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:args[3]))
