import Foundation
import CoreGraphics
import ImageIO
// Original geometric bookmark mark; no source bitmap or third-party artwork.
let context=CGContext(data:nil,width:1024,height:1024,bitsPerComponent:8,bytesPerRow:4096,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipLast.rawValue)!
context.setFillColor(CGColor(red:0.196,green:0.353,blue:0.290,alpha:1));context.fill(CGRect(x:0,y:0,width:1024,height:1024))
context.setStrokeColor(CGColor(red:0.573,green:0.737,blue:0.624,alpha:1));context.setLineWidth(42);context.setLineJoin(.round)
let back=CGPath(roundedRect:CGRect(x:238,y:220,width:370,height:576),cornerWidth:36,cornerHeight:36,transform:nil);context.addPath(back);context.strokePath()
context.setFillColor(CGColor(red:0.992,green:0.965,blue:0.890,alpha:1))
let mark=CGMutablePath();mark.move(to:CGPoint(x:400,y:224));mark.addLine(to:CGPoint(x:400,y:776));mark.addQuadCurve(to:CGPoint(x:432,y:808),control:CGPoint(x:400,y:808));mark.addLine(to:CGPoint(x:716,y:808));mark.addQuadCurve(to:CGPoint(x:748,y:776),control:CGPoint(x:748,y:808));mark.addLine(to:CGPoint(x:748,y:224));mark.addLine(to:CGPoint(x:574,y:350));mark.closeSubpath();context.addPath(mark);context.fillPath()
let target=URL(fileURLWithPath:CommandLine.arguments[1]);let destination=CGImageDestinationCreateWithURL(target as CFURL,"public.png" as CFString,1,nil)!
CGImageDestinationAddImage(destination,context.makeImage()!,[kCGImagePropertyPNGDictionary:[kCGImagePropertyPNGDescription:"Original geometric Shiji bookmark. Source: Tests/make_icon.swift; sage #325a4a / #92bc9f, cream #fdf6e3. 1024px opaque RGB canvas; two bookmark forms."]] as CFDictionary);assert(CGImageDestinationFinalize(destination))
