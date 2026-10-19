import SwiftUI
import PhotosUI
import UniformTypeIdentifiers

private extension Color {
    init(coverHex:String){let n=UInt32(coverHex.dropFirst(),radix:16) ?? 0;self.init(red:Double((n>>16)&255)/255,green:Double((n>>8)&255)/255,blue:Double(n&255)/255)}
}

/// Native geometry/typography, not a WebView copy of the desktop poster.
struct StudioPoster:View {
    let resource:Resource
    @Environment(\.dynamicTypeSize) private var typeSize
    private var c:[String:Any]{CoverConfiguration.read(resource.raw["coverConfig"])}
    private var direction:(style:String,template:String,palette:String){CoverConfiguration.direction(resource)}
    private var title:String{let custom=c["customTitle"] as? String ?? "";return custom.isEmpty ? resource.title : custom}
    private var subtitle:String{CoverConfiguration.subtitle(resource,automatic:!(direction.style=="developer" && direction.template=="a"))}
    private var alignment:Alignment {
        switch c["titlePosition"] as? String ?? "auto"{case "top":return .topLeading;case "center":return .center;case "bottom":return .bottomLeading;default:break}
        switch direction.style{case "spatial","kinetic":return .bottomLeading;case "minimal":return direction.template=="c" ? .center : .bottomLeading;default:return .topLeading}
    }
    var body:some View {
        GeometryReader{g in
            let colors=CoverConfiguration.colors(c,palette:direction.palette),bg=Color(coverHex:colors.background),ink=Color(coverHex:colors.foreground),accent=Color(coverHex:colors.accent),w=g.size.width,h=g.size.height
            let units=title.unicodeScalars.reduce(0.0){$0+((0x3400...0x9fff).contains($1.value) ? 1 : 0.55)}
            let scale=(c["density"] as? String)=="compact" ? 0.72 : (c["density"] as? String)=="bold" ? 1.1 : 1.0
            let font=typeSize.isAccessibilitySize ? 20.0 : max(16,min(62,w*min(0.19,0.8/max(4,units/ceil(max(1,units)/10)))))*scale
            ZStack {
                bg
                subject(width:w,height:h,bg:bg,ink:ink,accent:accent).accessibilityHidden(true)
                VStack{HStack{Text(resource.sourceHost).lineLimit(1);Spacer(minLength:8);Text(resource.text("category")).lineLimit(1)}.font(.system(size:max(9,w*0.025),weight:.semibold));Spacer();HStack{Text(resource.names("tags").prefix(3).joined(separator:" · ")).lineLimit(1);Spacer()}.font(.system(size:max(9,w*0.025),weight:.medium))}.padding(18)
                VStack(alignment:alignment == .center ? .center : .leading,spacing:10){
                    Text(title).font(.system(size:font,weight:.heavy)).tracking(-0.5).lineLimit(typeSize.isAccessibilitySize ? 2 : 4).minimumScaleFactor(0.65).multilineTextAlignment(alignment == .center ? .center : .leading)
                    if !subtitle.isEmpty {Text(subtitle).font(.system(size:max(11,w*0.029))).lineLimit(typeSize.isAccessibilitySize ? 1 : 2)}
                }.padding(direction.style=="spatial" || direction.style=="kinetic" && direction.template=="b" ? 6 : 0).background(direction.style=="spatial" || direction.style=="kinetic" && direction.template=="b" ? bg : .clear).padding(.horizontal,22).padding(.top,alignment == .topLeading ? 53 : 20).padding(.bottom,alignment == .bottomLeading ? 43 : 20).frame(maxWidth:.infinity,maxHeight:.infinity,alignment:alignment)
            }.foregroundStyle(ink).frame(width:w,height:h).clipped().accessibilityHidden(true)
        }
    }
    @ViewBuilder private func subject(width:CGFloat,height:CGFloat,bg:Color,ink:Color,accent:Color)->some View {
        let style=direction.style,t=direction.template
        switch style {
        case "editorial":
            if t=="a"{Rectangle().fill(ink).frame(width:width*0.86,height:2).position(x:width*0.5,y:height*0.19)}
            else if t=="b"{Text(String(title.prefix(2))).font(.system(size:width*0.58,weight:.black)).foregroundStyle(accent).rotationEffect(.degrees(-9));Rectangle().fill(bg).overlay{Rectangle().stroke(ink,lineWidth:1)}.padding(.horizontal,width*0.08).padding(.vertical,height*0.22).rotationEffect(.degrees(4)).shadow(color:.black.opacity(0.2),radius:8,x:4,y:10)}
            else{Rectangle().fill(accent).frame(width:width*0.7,height:height*0.6).rotationEffect(.degrees(13)).offset(x:width*0.1,y:8);Rectangle().fill(bg).overlay{Rectangle().stroke(ink,lineWidth:1)}.frame(width:width*0.79,height:height*0.65).rotationEffect(.degrees(-5))}
        case "spatial":
            if t=="a"{Circle().fill(RadialGradient(colors:[.white,accent,bg,.black],center:.topLeading,startRadius:0,endRadius:width*0.6)).frame(width:width*0.52).shadow(color:.black.opacity(0.3),radius:14,x:12,y:18).offset(x:width*0.16,y:-height*0.08);Ellipse().stroke(ink.opacity(0.7),lineWidth:6).frame(width:width*0.67,height:height*0.3).rotationEffect(.degrees(-25)).offset(x:width*0.14,y:-height*0.07)}
            else if t=="b"{ForEach(0..<3){i in Rectangle().fill(i==2 ? ink : i==0 ? accent : bg).overlay{Rectangle().stroke(ink,lineWidth:1)}.frame(width:width*0.45,height:height*0.3).rotation3DEffect(.degrees(35),axis:(x:1,y:0,z:0)).rotationEffect(.degrees(-25)).shadow(color:.black.opacity(0.22),radius:7,x:5,y:8).offset(x:width*0.18-CGFloat(i)*12,y:-height*0.23+CGFloat(i)*27)}}
            else{ForEach(0..<5){i in Rectangle().fill(i==4 ? bg : accent).overlay{Rectangle().stroke(ink,lineWidth:1)}.frame(width:width*0.17,height:height*0.19).rotation3DEffect(.degrees(45),axis:(x:1,y:0,z:0)).rotationEffect(.degrees(-30)).shadow(color:ink.opacity(0.6),radius:0,x:6,y:8).offset(x:width*0.12+CGFloat(i%2)*width*0.2,y:-height*0.3+CGFloat(i/2)*height*0.2)}}
        case "developer":
            if t=="a"{VStack(alignment:.leading,spacing:8){Text(resource.text("language")).font(.caption.monospaced());ForEach(Array(resource.coverLines.prefix(5).enumerated()),id:\.offset){_,line in Text(line.isEmpty ? " " : line).font(.system(size:max(9,width*0.027),design:.monospaced)).lineLimit(1)}}.padding(14).frame(width:width*0.85,height:height*0.42,alignment:.topLeading).foregroundStyle(Color(coverHex:"#c5ff43")).background(Color(coverHex:"#17191c"),in:RoundedRectangle(cornerRadius:6)).rotationEffect(.degrees(-3)).shadow(color:.black.opacity(0.25),radius:8,x:6,y:9).offset(y:height*0.19)}
            else if t=="b"{Text(String(title.prefix(2))).font(.system(size:width*0.53,weight:.black)).foregroundStyle(accent).rotationEffect(.degrees(-13)).offset(x:width*0.21,y:-height*0.03);Rectangle().stroke(ink,lineWidth:1.5).frame(width:width*0.83,height:height*0.58);if !resource.text("language").isEmpty{Text(resource.text("language")).font(.caption.monospaced().bold()).padding(9).foregroundStyle(bg).background(ink).rotationEffect(.degrees(-8)).offset(x:width*0.22,y:height*0.32)}}
            else{VStack(alignment:.leading,spacing:10){ForEach(0..<4){i in Rectangle().fill(i%2==0 ? bg : accent).frame(width:width*(i==2 ? 0.15 : 0.22),height:height*0.04).padding(.leading,i%2==0 ? 0 : 12)}}.padding(12).frame(width:width*0.33,height:height*0.45).background(ink).rotation3DEffect(.degrees(-18),axis:(x:0,y:1,z:0)).shadow(color:.black.opacity(0.25),radius:8,x:6,y:10).offset(x:width*0.27,y:-height*0.02)}
        case "kinetic":
            if t=="a"{VStack(spacing:0){ForEach(0..<3){_ in Text(title).font(.system(size:width*0.16,weight:.black)).lineLimit(1)}}.foregroundStyle(ink.opacity(0.15)).rotationEffect(.degrees(-9)).offset(y:-height*0.15)}
            else if t=="b"{Ellipse().stroke(ink,lineWidth:width*0.06).frame(width:width*0.63,height:height*0.49).rotationEffect(.degrees(-30)).offset(x:width*0.2,y:-height*0.08);Ellipse().stroke(accent,lineWidth:width*0.05).frame(width:width*0.5,height:height*0.33).rotationEffect(.degrees(29)).offset(x:-width*0.03,y:-height*0.2)}
            else{HStack(spacing:10){ForEach(0..<5){i in Capsule().stroke(ink,lineWidth:8).background(i%2==0 ? accent : .clear,in:Capsule()).frame(width:width*0.13,height:height*(i%2==0 ? 0.35 : 0.17))}}.rotationEffect(.degrees(-15)).offset(y:-height*0.16)}
        default:
            if t=="a"{Circle().stroke(ink.opacity(0.55),lineWidth:1).frame(width:width*0.42).offset(y:-height*0.09);Circle().stroke(ink.opacity(0.3),lineWidth:1).frame(width:width*0.32).offset(y:-height*0.09)}
            else if t=="b"{Rectangle().stroke(ink,lineWidth:1).frame(width:width*0.7,height:height*0.63).rotationEffect(.degrees(4))}
            else{Rectangle().fill(ink.opacity(0.3)).frame(width:1,height:height*0.68)}
        }
    }
}

struct FocalCoverImage:View {
    let image:UIImage
    let config:[String:Any]
    var body:some View{GeometryReader{g in
        let fit=config["imageFit"] as? String=="fit",x=(config["imageX"] as? NSNumber)?.doubleValue ?? 50,y=(config["imageY"] as? NSNumber)?.doubleValue ?? 50
        let scale=fit ? min(g.size.width/image.size.width,g.size.height/image.size.height) : max(g.size.width/image.size.width,g.size.height/image.size.height)
        let w=image.size.width*scale,h=image.size.height*scale
        Image(uiImage:image).resizable().frame(width:w,height:h).position(x:(g.size.width-w)*x/100+w/2,y:(g.size.height-h)*y/100+h/2)
    }.clipped().accessibilityHidden(true)}
}

/// Immutable attachment IDs keep decoded image work out of slider/body updates.
struct StudioLocalCoverImage:View {
    let resource:Resource
    let url:URL?
    @State private var loaded:URL?
    @State private var image:UIImage?
    private var c:[String:Any]{CoverConfiguration.read(resource.raw["coverConfig"])}
    var body:some View{Group{
        if let image,loaded==url{FocalCoverImage(image:image,config:c).overlay{StudioCoverText(resource:resource)}}
        else if CoverConfiguration.future(resource.raw["coverConfig"]) || c["style"] as? String=="v5"{NativeResourceCover(resource:resource)}
        else{StudioPoster(resource:resource)}
    }.task(id:url){image=nil;loaded=nil;guard let url else{return};let decoded=await Task.detached{LocalImage.image(url:url)}.value;guard !Task.isCancelled else{return};image=decoded;loaded=url}}
}

struct StudioCoverText:View {
    let resource:Resource
    var body:some View{let c=CoverConfiguration.read(resource.raw["coverConfig"]),colors=CoverConfiguration.colors(c,palette:CoverConfiguration.direction(resource).palette),title=c["customTitle"] as? String ?? "",subtitle=c["customSubtitle"] as? String ?? ""
        if !title.isEmpty || !subtitle.isEmpty{VStack(alignment:.leading,spacing:6){if !title.isEmpty{Text(title).font(.title2.bold()).lineLimit(3)};if !subtitle.isEmpty{Text(subtitle).font(.caption).lineLimit(2)}}.padding(12).foregroundStyle(Color(coverHex:colors.foreground)).background(Color(coverHex:colors.background)).padding(16).frame(maxWidth:.infinity,maxHeight:.infinity,alignment:c["titlePosition"] as? String=="top" ? .topLeading : c["titlePosition"] as? String=="center" ? .center : .bottomLeading)}
    }
}

struct NativeCoverStudio:View {
    @EnvironmentObject private var library:MobileLibrary
    @Environment(\.dismiss) private var dismiss
    private let onSaved:()->Void
    @State private var baseline:Resource
    private var resource:Resource{baseline}
    @State private var draft:[String:Any]?
    @State private var coverID:String
    @State private var pending:(Data,String,String)?
    @State private var pendingImage:UIImage?
    @State private var reading=false
    @State private var saving=false
    @State private var message:String?
    @State private var importer=false
    @State private var photo:PhotosPickerItem?
    @State private var importTask:Task<Void,Never>?
    init(resource:Resource,onSaved:@escaping ()->Void={}){self.onSaved=onSaved;_baseline=State(initialValue:resource);_draft=State(initialValue:try? CoverConfiguration.normalize(resource.raw["coverConfig"]));_coverID=State(initialValue:resource.text("coverId"))}
    private var c:[String:Any]{CoverConfiguration.read(draft)}
    private var unsupported:Bool{CoverConfiguration.future(draft)}
    private var preview:Resource{var raw=resource.raw;raw["coverConfig"]=draft ?? NSNull() as Any;raw["coverId"]=coverID;return Resource(raw:raw)}
    private func set(_ key:String,_ value:Any){guard !unsupported,!saving else{return};var next=draft ?? CoverConfiguration.defaults;next[key]=value;draft=next}
    private func string(_ key:String)->Binding<String>{Binding(get:{(unsupported ? CoverConfiguration.defaults[key] : draft?[key] ?? CoverConfiguration.defaults[key]) as? String ?? ""},set:{set(key,$0)})}
    private func number(_ key:String)->Binding<Double>{Binding(get:{(c[key] as? NSNumber)?.doubleValue ?? 50},set:{set(key,$0)})}
    private let styles=[("auto","自动"),("editorial","Editorial"),("spatial","Spatial"),("developer","Developer"),("kinetic","Kinetic"),("minimal","Minimal"),("v5","原版 V5")]
    var body:some View {
        NavigationStack{Form{
            Section{Group{if let pendingImage,CoverConfiguration.usesDraftImage(draft){FocalCoverImage(image:pendingImage,config:c).overlay{StudioCoverText(resource:preview)}}else{LocalCover(resource:preview)}}.frame(height:250).clipShape(RoundedRectangle(cornerRadius:14)).listRowInsets(EdgeInsets(top:12,leading:0,bottom:12,trailing:0))
                Text("封面文字独立保存，不修改资源原标题、标签或备注。").font(.caption).foregroundStyle(.secondary)}
            if unsupported{Section{Text("此封面来自更新版本。保留当前设置，或恢复自动后重新设计。").foregroundStyle(.secondary)}}
            Group{
                Section("风格与构图"){
                    ScrollView(.horizontal){HStack(spacing:10){ForEach(styles,id:\.0){key,label in Button{set("style",key)}label:{VStack{thumbnail(key).frame(width:92,height:68).clipShape(RoundedRectangle(cornerRadius:7));Text(label).font(.caption)}.padding(5).background((c["style"] as? String)==key ? Color.accentColor.opacity(0.2) : .clear,in:RoundedRectangle(cornerRadius:9))}.buttonStyle(.plain).accessibilityLabel(label).accessibilityAddTraits((c["style"] as? String)==key ? .isSelected : [])}}}
                    Picker("构图",selection:string("template")){Text("自动").tag("auto");Text("1").tag("a");Text("2").tag("b");Text("3").tag("c")}.pickerStyle(.segmented).disabled(c["style"] as? String=="v5")
                    Button("换一版构图",systemImage:"arrow.triangle.2.circlepath"){let seed=(c["seed"] as? NSNumber)?.uint64Value ?? 0;set("template","auto");set("seed",(seed+1)&0xffffffff)}.disabled(c["style"] as? String=="v5")
                }
                Section("颜色"){
                    Picker("配色",selection:string("palette")){Text("推荐").tag("auto");Text("荧光绿").tag("acid");Text("纸白").tag("paper");Text("紫色").tag("violet");Text("青色").tag("cyan");Text("珊瑚").tag("coral");Text("墨黑").tag("ink")}
                    TextField("自定义主色 #RRGGBB",text:string("primary")).accessibilityIdentifier("cover-primary").textInputAutocapitalization(.never).autocorrectionDisabled()
                    Button("恢复推荐主色"){set("primary","")}
                }
                Section("封面文字"){
                    TextField("封面标题 · 沿用资源名",text:string("customTitle"),axis:.vertical).lineLimit(1...4).accessibilityIdentifier("cover-custom-title")
                    TextField("副标题 · 使用内容摘要",text:string("customSubtitle"),axis:.vertical).lineLimit(1...4).accessibilityIdentifier("cover-custom-subtitle")
                    Picker("标题位置",selection:string("titlePosition")){Text("跟随构图").tag("auto");Text("顶部").tag("top");Text("居中").tag("center");Text("底部").tag("bottom")}
                    Picker("排版密度",selection:string("density")){Text("均衡").tag("balanced");Text("紧凑").tag("compact");Text("醒目").tag("bold")}
                }
                Section("图片"){
                    Picker("封面来源",selection:string("imageSource")){Text("自动 · 真实封面优先").tag("auto");Text("本地图片").tag("image");Text("网站预览").tag("website");Text("程序化海报").tag("poster")}
                    Picker("图片附件",selection:Binding(get:{coverID},set:{coverID=$0;pending=nil;pendingImage=nil;set("imageSource","image")})){Text("未选择").tag("");ForEach(Array(resource.attachments.filter{($0["mime"] as? String ?? "").hasPrefix("image/")}.enumerated()),id: \.offset){_,a in Text(a["name"] as? String ?? "图片").tag(a["id"] as? String ?? "")}}
                    PhotosPicker(selection:$photo,matching:.images){Label("从照片选择",systemImage:"photo")}
                    Button("从文件选择",systemImage:"folder"){importer=true}
                    if let pending{Text("\(pending.1) · 保存时才加入附件").font(.caption).foregroundStyle(.secondary)}
                    Picker("适配",selection:string("imageFit")){Text("填充裁剪").tag("fill");Text("完整显示").tag("fit")}
                    VStack(alignment:.leading){Text("横向焦点");Slider(value:number("imageX"),in:0...100,step:1)}.accessibilityElement(children:.combine)
                    VStack(alignment:.leading){Text("纵向焦点");Slider(value:number("imageY"),in:0...100,step:1)}.accessibilityElement(children:.combine)
                }
            }.disabled(unsupported || saving || reading)
            Section{Button("恢复自动封面"){importTask?.cancel();reading=false;draft=nil;coverID=resource.text("coverId");pending=nil;pendingImage=nil;message=nil}.disabled(saving)}
            if reading{Section{ProgressView("正在读取图片…")}}
            if let message{Section{Text(message).foregroundStyle(.red).accessibilityLabel("保存未完成："+message)}}
        }.navigationTitle("封面设计").navigationBarTitleDisplayMode(.inline)
            .toolbar{ToolbarItem(placement:.cancellationAction){Button("取消"){dismiss()}.disabled(saving)};ToolbarItem(placement:.confirmationAction){Button(saving ? "保存中…" : "保存"){commit()}.disabled(saving || reading || unsupported)}}
            .interactiveDismissDisabled(saving)
            .fileImporter(isPresented:$importer,allowedContentTypes:[.image]){result in switch result{case .success(let url):importFile(url);case .failure(let e):message=e.localizedDescription}}
            .onChange(of:photo){_,value in guard let value else{return};importTask?.cancel();reading=true;importTask=Task{do{let data=try await value.loadTransferable(type:Data.self);guard !Task.isCancelled else{return};guard let data else{reading=false;message="照片无法读取，请重新选择。";return};accept(data,name:"照片.jpg",convertPhoto:true)}catch{if !Task.isCancelled{reading=false;message=error.localizedDescription}}}}
            .onDisappear{importTask?.cancel()}
        }
    }
    private func thumbnail(_ style:String)->some View{var raw=resource.raw;raw["coverConfig"]=["style":style,"imageSource":"poster"];return Group{if style=="v5"{NativeResourceCover(resource:Resource(raw:raw))}else{StudioPoster(resource:Resource(raw:raw))}}.frame(width:360,height:266).scaleEffect(92.0/360,anchor:.topLeading).frame(width:92,height:68,alignment:.topLeading).clipped().accessibilityHidden(true)}
    private func accept(_ data:Data,name:String,convertPhoto:Bool=false){
        guard !Task.isCancelled else{return}
        do{var bytes=data,mime=LibraryFiles.detectedMIME(data),name=name
            if convertPhoto && !["image/png","image/jpeg","image/gif","image/webp"].contains(mime){guard data.count<=20*1024*1024,let image=LocalImage.image(data:data),let encoded=image.jpegData(compressionQuality:0.94)else{throw fail("照片无法读取，请选择其他图片。")};bytes=encoded;mime="image/jpeg";name="照片.jpg"}
            try CoverConfiguration.validateImage(bytes,mime:mime);guard let image=LocalImage.image(data:bytes)else{throw fail("图片无法解码。")};pending=(bytes,name,mime);pendingImage=image;coverID="";set("imageSource","image");reading=false;message=nil
        }catch{reading=false;message=error.localizedDescription}
    }
    private func importFile(_ url:URL){importTask?.cancel();reading=true;importTask=Task{do{let data=try await Task.detached{let allowed=url.startAccessingSecurityScopedResource();defer{if allowed{url.stopAccessingSecurityScopedResource()}};guard (try url.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0)<=5*1024*1024 else{throw fail("封面图片超过 5 MB。")};return try Data(contentsOf:url)}.value;guard !Task.isCancelled else{return};accept(data,name:url.lastPathComponent)}catch{if !Task.isCancelled{reading=false;message=error.localizedDescription}}}}
    private func commit(){guard !saving,!reading,!unsupported,let files=library.files else{return};do{_ = try CoverConfiguration.normalize(draft)}catch{message=error.localizedDescription;return};saving=true;message=nil;let config=draft,chosen=coverID,upload=pending,source=resource
        Task{do{_ = try await Task.detached{try files.updateCover(source.id,config:config,coverID:chosen,expectedConfig:source.raw["coverConfig"],expectedCoverID:source.text("coverId"),upload:upload)}.value;library.reload();onSaved();UIAccessibility.post(notification:.announcement,argument:"封面已保存");saving=false;dismiss()}catch{saving=false;message=error.localizedDescription}}
    }
}
