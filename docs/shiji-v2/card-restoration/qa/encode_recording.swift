import Foundation
import AVFoundation
import AppKit
struct Frame:Decodable{let path:String;let time:Double}
guard CommandLine.arguments.count == 3 else { fatalError("Usage: swift encode_recording.swift frames.json output.mp4") }
let frames=try JSONDecoder().decode([Frame].self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
let first=NSImage(contentsOfFile:frames[0].path)!.cgImage(forProposedRect:nil,context:nil,hints:nil)!
let width=first.width+(first.width%2),height=first.height+(first.height%2)
let output=URL(fileURLWithPath:CommandLine.arguments[2])
let writer=try AVAssetWriter(outputURL:output,fileType:.mp4)
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height])
let adapter=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height])
writer.add(input);writer.startWriting();writer.startSession(atSourceTime:.zero)
for frame in frames {
 while !input.isReadyForMoreMediaData {Thread.sleep(forTimeInterval:0.002)}
 var buffer:CVPixelBuffer?;CVPixelBufferPoolCreatePixelBuffer(nil,adapter.pixelBufferPool!,&buffer)
 CVPixelBufferLockBaseAddress(buffer!,[])
 let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer!),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer!),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
 context.setFillColor(NSColor.black.cgColor);context.fill(CGRect(x:0,y:0,width:width,height:height))
 let image=NSImage(contentsOfFile:frame.path)!.cgImage(forProposedRect:nil,context:nil,hints:nil)!
 context.draw(image,in:CGRect(x:0,y:height-image.height,width:image.width,height:image.height));CVPixelBufferUnlockBaseAddress(buffer!,[])
 guard adapter.append(buffer!,withPresentationTime:CMTime(seconds:(frame.time-frames[0].time)/1000,preferredTimescale:1000))else{fatalError(writer.error!.localizedDescription)}
}
input.markAsFinished();let semaphore=DispatchSemaphore(value:0);writer.finishWriting{semaphore.signal()};semaphore.wait()
guard writer.status == .completed else{fatalError(writer.error!.localizedDescription)}
print("Encoded",frames.count,"actual CUA frames at recorded timestamps;",width,"x",height)
