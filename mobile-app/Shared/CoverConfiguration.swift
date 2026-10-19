import Foundation
import CoreFoundation
#if canImport(ImageIO)
import ImageIO
#endif

/// The same optional resource value as desktop; indexes and UI state are not authority.
enum CoverConfiguration {
    static let defaults:[String:Any] = ["version":1,"style":"auto","template":"auto","seed":0,"palette":"auto","primary":"","customTitle":"","customSubtitle":"","titlePosition":"auto","density":"balanced","imageSource":"auto","imageFit":"fill","imageX":50,"imageY":50]
    static let palettes = ["acid":"#c5ff43","paper":"#f3efdf","violet":"#b39bff","cyan":"#65e2e4","coral":"#ff8d72","ink":"#17191c"]
    private static let choices = ["style":["auto","editorial","spatial","developer","kinetic","minimal","v5"],"template":["auto","a","b","c"],"palette":["auto","acid","paper","violet","cyan","coral","ink"],"titlePosition":["auto","top","center","bottom"],"density":["balanced","compact","bold"],"imageSource":["auto","image","website","poster"],"imageFit":["fill","fit"]]
    private static func number(_ value:Any?) -> Double? {
        guard let n=value as? NSNumber,CFGetTypeID(n) != CFBooleanGetTypeID(),n.doubleValue.isFinite else{return nil};return n.doubleValue
    }
    private static func jsonValue(_ value:Any,depth:Int=1) throws {
        guard depth<=4 else{throw fail("封面设置层级过深。")}
        if let map=value as? [String:Any]{for child in map.values{try jsonValue(child,depth:depth+1)};return}
        if let array=value as? [Any]{for child in array{try jsonValue(child,depth:depth+1)};return}
        if value is NSNull || value is String{return}
        if let n=value as? NSNumber,n.doubleValue.isFinite{return}
        throw fail("封面设置必须是有限 JSON 数据。")
    }
    private static func bounded(_ value:[String:Any]) throws -> Data {
        try jsonValue(value);let data=try JSONSerialization.data(withJSONObject:value,options:.withoutEscapingSlashes)
        guard data.count<=8192 else{throw fail("封面设置超过 8 KiB。")};return data
    }
    static func normalize(_ value:Any?) throws -> [String:Any]? {
        guard let value,!(value is NSNull) else{return nil}
        guard let value=value as? [String:Any] else{throw fail("封面设置必须是对象。")}
        let data=try bounded(value)
        guard let version=number(value["version"] ?? 1),version>=1,version<=2147483647,version.rounded(.towardZero)==version else{throw fail("封面设置版本无效。")}
        let cloned=try JSONSerialization.jsonObject(with:data) as! [String:Any]
        if version>1{return cloned}
        var result=defaults;for (key,value) in cloned{result[key]=value}
        for (key,options) in choices{guard let text=result[key] as? String,options.contains(text)else{throw fail("封面选项无效："+key)}}
        guard let seed=number(result["seed"]),seed>=0,seed<=4294967295,seed.rounded(.towardZero)==seed else{throw fail("封面种子无效。")}
        for (key,max) in [("customTitle",200),("customSubtitle",240)]{guard let text=result[key] as? String,text.unicodeScalars.count<=max else{throw fail("封面文字过长或无效。")}}
        guard let primary=result["primary"] as? String,primary.isEmpty || primary.range(of:"^#[0-9a-fA-F]{6}$",options:.regularExpression) != nil else{throw fail("封面主色必须是六位十六进制颜色。")}
        result["primary"]=primary.lowercased()
        for key in ["imageX","imageY"]{guard let n=number(result[key]),n>=0,n<=100 else{throw fail("封面图片位置无效。")}}
        _ = try bounded(result);return result
    }
    static func future(_ value:Any?) -> Bool {guard let c=try? normalize(value),let n=number(c["version"]) else{return false};return n>1}
    static func read(_ value:Any?) -> [String:Any] {guard let c=try? normalize(value),!future(c)else{return defaults};return c}
    static func equal(_ a:Any?,_ b:Any?) throws -> Bool {
        try JSONSerialization.data(withJSONObject:[normalize(a) ?? NSNull() as Any],options:.sortedKeys)==JSONSerialization.data(withJSONObject:[normalize(b) ?? NSNull() as Any],options:.sortedKeys)
    }
    static func direction(_ r:Resource) -> (style:String,template:String,palette:String) {
        let c=read(r.raw["coverConfig"]),site=r.sourceHost.replacingOccurrences(of:"^www\\.",with:"",options:.regularExpression),text=([r.title,r.text("description"),r.text("category"),r.text("language")]+r.names("tags")).joined(separator:" ")
        func match(_ pattern:String)->Bool{text.range(of:pattern,options:[.regularExpression,.caseInsensitive]) != nil}
        let rules:[(String,String,Int,Bool)] = [
            ("developer","b",10,r.text("category")=="开发工具"),("editorial","c",10,["UI / 设计","美术素材"].contains(r.text("category"))),
            ("developer","a",100,r.text("kind")=="code"),("editorial","b",100,r.text("kind")=="prompt"),
            ("developer","b",40,["github.com","gitlab.com","codeberg.org"].contains(site)),
            ("developer","c",60,match("\\breact\\b|components?|组件|设计系统") || ["reactbits.dev","ui.shadcn.com"].contains(site)),
            ("spatial","b",80,match("robot|机器人|机械|关节")),
            ("spatial","c",55,["huggingface.co","openai.com","anthropic.com"].contains(site) || match("\\b(AI|ML|LLM)\\b|人工智能|机器学习")),
            ("spatial","a",65,["polyhaven.com","spline.design"].contains(site) || match("\\b3d\\b|三维|建模|材质")),
            ("kinetic","a",75,["motionsites.ai","gsap.com"].contains(site) || match("motion|animation|gsap|动效|动画")),
            ("kinetic","b",80,match("kinetic|动态字体|逐帧")),("kinetic","c",60,site=="freesound.org" || match("音频|声效|\\baudio\\b")),
            ("editorial","c",50,site=="recent.co" || match("灵感|字体|排版|配色|inspiration|typograph|palette")),
            ("minimal","a",20,!r.text("coverId").isEmpty || !r.text("thumbnail").isEmpty || r.attachments.contains{($0["mime"] as? String ?? "").hasPrefix("image/")}),
            ("minimal","b",25,r.text("kind")=="file" && r.text("coverId").isEmpty && r.text("thumbnail").isEmpty && !r.attachments.contains{($0["mime"] as? String ?? "").hasPrefix("image/")})]
        var rows=["editorial":("a",1),"spatial":("a",0),"developer":("b",0),"kinetic":("a",0),"minimal":("c",0)]
        for (style,template,score,matched) in rules where matched{if score>rows[style]!.1{rows[style]=(template,score)}}
        let explicit=c["style"] as? String ?? "auto"
        let style=rows[explicit] != nil ? explicit : ["editorial","spatial","developer","kinetic","minimal"].max{rows[$0]!.1<rows[$1]!.1}!
        let chosen=c["template"] as? String ?? "auto",seed=Int(number(c["seed"]) ?? 0),base=["a","b","c"].firstIndex(of:rows[style]!.0) ?? 0
        let template=chosen=="auto" ? ["a","b","c"][(base+seed)%3] : chosen
        let automatic=["editorial":"paper","spatial":"violet","developer":"acid","kinetic":"coral","minimal":"ink"][style]!
        let palette=c["palette"] as? String ?? "auto"
        return (style,template,palette=="auto" ? automatic : palette)
    }
    static func subtitle(_ resource:Resource,automatic:Bool=true) -> String { let value=read(resource.raw["coverConfig"])["customSubtitle"] as? String ?? "";return value.isEmpty ? (automatic ? resource.coverExcerpt : "") : value }
    static func usesDraftImage(_ value:Any?) -> Bool { ["auto","image"].contains(read(value)["imageSource"] as? String ?? "auto") }
    static func colors(_ c:[String:Any],palette:String="acid") -> (background:String,foreground:String,accent:String) {
        let selected=c["palette"] as? String ?? "auto",primary=c["primary"] as? String ?? "",bg=primary.isEmpty ? palettes[selected=="auto" ? palette : selected] ?? palettes["acid"]! : primary
        func luminance(_ hex:String)->Double{let n=UInt32(hex.dropFirst(),radix:16) ?? 0;return [Double((n>>16)&255),Double((n>>8)&255),Double(n&255)].enumerated().reduce(0){sum,entry in let v=entry.element/255;return sum+(v<=0.04045 ? v/12.92 : pow((v+0.055)/1.055,2.4))*[0.2126,0.7152,0.0722][entry.offset]}}
        let l=luminance(bg),dark=(l+0.05)/(luminance("#111111")+0.05),light=1.05/(l+0.05)
        return (bg,dark>=4.5 ? "#111111" : light>=4.5 ? "#ffffff" : "#000000",bg==palettes["violet"] ? palettes["acid"]! : palettes["violet"]!)
    }
    static func validateImage(_ bytes:Data,mime:String) throws {
        guard !bytes.isEmpty,bytes.count<=5*1024*1024,["image/png","image/jpeg","image/gif","image/webp"].contains(mime),LibraryFiles.detectedMIME(bytes)==mime else{throw fail("请选择 5 MB 以内的 PNG、JPEG、GIF 或 WebP 图片。")}
        #if canImport(ImageIO)
        guard let source=CGImageSourceCreateWithData(bytes as CFData,[kCGImageSourceShouldCache:false] as CFDictionary),let p=CGImageSourceCopyPropertiesAtIndex(source,0,nil) as? [CFString:Any],let w=p[kCGImagePropertyPixelWidth] as? NSNumber,let h=p[kCGImagePropertyPixelHeight] as? NSNumber,w.intValue>0,h.intValue>0,w.doubleValue*h.doubleValue<=67108864,CGImageSourceCreateThumbnailAtIndex(source,0,[kCGImageSourceCreateThumbnailFromImageAlways:true,kCGImageSourceThumbnailMaxPixelSize:1024] as CFDictionary) != nil else{throw fail("图片文件无法验证，未保存。")}
        #else
        throw fail("当前环境无法验证图片，未保存。")
        #endif
    }
}
