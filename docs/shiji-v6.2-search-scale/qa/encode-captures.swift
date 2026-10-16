import AppKit
import AVFoundation
struct Frame:Decodable{let file:String;let ms:Double}
let root=URL(fileURLWithPath:CommandLine.arguments[1]),out=URL(fileURLWithPath:CommandLine.arguments[2])
let frames=try JSONDecoder().decode([Frame].self,from:Data(contentsOf:root.appendingPathComponent("frames.json")))
let first=NSImage(contentsOf:root.appendingPathComponent(frames[0].file))!;let cg=first.cgImage(forProposedRect:nil,context:nil,hints:nil)!
let width=cg.width/2*2,height=cg.height/2*2
let writer=try AVAssetWriter(outputURL:out,fileType:.mp4),input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height])
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height])
writer.add(input);writer.startWriting();writer.startSession(atSourceTime:.zero)
for frame in frames{
 while !input.isReadyForMoreMediaData{Thread.sleep(forTimeInterval:0.002)}
 let image=NSImage(contentsOf:root.appendingPathComponent(frame.file))!.cgImage(forProposedRect:nil,context:nil,hints:nil)!
 var buffer:CVPixelBuffer?;CVPixelBufferCreate(kCFAllocatorDefault,width,height,kCVPixelFormatType_32ARGB,nil,&buffer)
 CVPixelBufferLockBaseAddress(buffer!,[])
 let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer!),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer!),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
 context.draw(image,in:CGRect(x:0,y:0,width:width,height:height));CVPixelBufferUnlockBaseAddress(buffer!,[])
 guard adaptor.append(buffer!,withPresentationTime:CMTime(value:Int64(frame.ms-frames[0].ms),timescale:1000)) else{fatalError("append failed")}
}
writer.endSession(atSourceTime:CMTime(value:Int64(frames.last!.ms-frames[0].ms+1000),timescale:1000));input.markAsFinished()
let done=DispatchSemaphore(value:0);writer.finishWriting{done.signal()};done.wait()
guard writer.status == .completed else{fatalError(String(describing:writer.error))}
print("encoded \(frames.count) actual UI captures; \(frames.last!.ms-frames[0].ms+1000) ms; \(width)x\(height)")
