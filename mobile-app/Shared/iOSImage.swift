#if os(iOS)
import UIKit
import ImageIO
// V2 semantic colors: Creative Tech dark and a contrast-safe system light variant.
enum NativePalette {
    private static func adaptive(_ light:UInt32,_ dark:UInt32)->UIColor {
        UIColor { traits in
            let value=traits.userInterfaceStyle == .dark ? dark : light
            return UIColor(red:CGFloat((value>>16)&255)/255,green:CGFloat((value>>8)&255)/255,blue:CGFloat(value&255)/255,alpha:1)
        }
    }
    static let background=adaptive(0xf7f7f2,0x0c0d10)
    static let surface=adaptive(0xffffff,0x15171d)
    static let raised=adaptive(0xededf0,0x1d2027)
    static let secondaryText=adaptive(0x555661,0x9d9eaa)
    static let onAccent=adaptive(0xffffff,0x0c0d10)
}
// Bound decoded pixels for large phone photos and library covers.
enum LocalImage {
    static func image(data:Data,maxPixels:Int=2048)->UIImage? {
        guard let source=CGImageSourceCreateWithData(data as CFData,[kCGImageSourceShouldCache:false] as CFDictionary)else{return nil}
        return thumbnail(source,maxPixels:maxPixels)
    }
    static func image(url:URL,maxPixels:Int=1024)->UIImage? {
        guard let source=CGImageSourceCreateWithURL(url as CFURL,[kCGImageSourceShouldCache:false] as CFDictionary)else{return nil}
        return thumbnail(source,maxPixels:maxPixels)
    }
    private static func thumbnail(_ source:CGImageSource,maxPixels:Int)->UIImage? {
        let options:[CFString:Any]=[kCGImageSourceCreateThumbnailFromImageAlways:true,kCGImageSourceCreateThumbnailWithTransform:true,kCGImageSourceThumbnailMaxPixelSize:maxPixels,kCGImageSourceShouldCacheImmediately:true]
        guard let cg=CGImageSourceCreateThumbnailAtIndex(source,0,options as CFDictionary)else{return nil};return UIImage(cgImage:cg)
    }
}
#endif
