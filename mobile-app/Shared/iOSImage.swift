#if os(iOS)
import UIKit
import ImageIO
// Opaque, sage-tinted supporting text and contrast-safe prominent button labels.
enum NativePalette {
    static let secondaryText=UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(red:0.682,green:0.737,blue:0.710,alpha:1)
            : UIColor(red:0.325,green:0.388,blue:0.361,alpha:1)
    }
    static let onAccent=UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(red:0.090,green:0.141,blue:0.106,alpha:1)
            : .white
    }
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
