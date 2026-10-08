import SwiftUI
import UniformTypeIdentifiers
import QuickLook
import PhotosUI
@MainActor final class MobileLibrary: ObservableObject {
    @Published var captureSequence=0
    @Published var introSequence=0
    @Published var editing=false
    @Published var resources=[Resource]()
    @Published var error:String?
    @Published var busy=false
    @Published var notice:String?
    var files:LibraryFiles?
    init(){do{files=try LibraryFiles(root:LibraryFiles.appRoot());reload()}catch{self.error=error.localizedDescription}}
    func reload(){do{resources=try files?.resources() ?? []}catch{self.error=error.localizedDescription}}
    @discardableResult func perform(_ action:() throws -> Void)->Bool {do{try action();reload();return true}catch{self.error=error.localizedDescription;return false}}
    @discardableResult func change(_ id:String,_ key:String,_ value:Any)->Bool{perform{try files?.set(id,key:key,value:value)}}
    func preview(_ url:URL) async -> ImportPlan? {
        guard let files else{return nil};busy=true;defer{busy=false}
        do{return try await Task.detached{let allowed=url.startAccessingSecurityScopedResource();defer{if allowed{url.stopAccessingSecurityScopedResource()}};let size=try url.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0;guard size<=PortableZIP.maxTotal else{throw fail("导入文件超过手机端 512 MB 上限。")};return try files.preview(Data(contentsOf:url))}.value}catch{self.error=error.localizedDescription;return nil}
    }
    func merge(_ plan:ImportPlan) async {guard let files else{return};busy=true;defer{busy=false};do{let count=try await Task.detached{try files.merge(plan)}.value;reload();notice="已加入 \(count) 条新资源，已有收藏保留。"}catch{self.error=error.localizedDescription}}
    func export() async -> Data? {guard let files else{return nil};busy=true;defer{busy=false};do{return try await Task.detached{try files.exportZIP()}.value}catch{self.error=error.localizedDescription;return nil}}
    func addFile(_ url:URL,id:String?=nil) async {
        guard let files else{return};busy=true;defer{busy=false}
        do{try await Task.detached{let allowed=url.startAccessingSecurityScopedResource();defer{if allowed{url.stopAccessingSecurityScopedResource()}};let size=try url.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0;guard size<=PortableZIP.maxFile else{throw fail("单个素材不能超过 64 MB。")};var bytes=try Data(contentsOf:url),name=url.lastPathComponent
                let type=UTType(filenameExtension:url.pathExtension)
                if type?.conforms(to:.image)==true,!LibraryFiles.detectedMIME(bytes).hasPrefix("image/"),let image=LocalImage.image(data:bytes),let jpeg=image.jpegData(compressionQuality:0.9){bytes=jpeg;name=url.deletingPathExtension().lastPathComponent+".jpg"}
                let mime=LibraryFiles.detectedMIME(bytes)
                if let id{try files.attach(bytes,name:name,mime:mime,id:id)}else{try files.capture(url:"",title:url.deletingPathExtension().lastPathComponent,text:"",attachment:(bytes,name,mime))}}.value;reload()}catch{self.error=error.localizedDescription}
    }
}
struct BackupDocument:FileDocument {
    static var readableContentTypes:[UTType]{[.zip]}
    var bytes:Data
    init(_ bytes:Data){self.bytes=bytes}
    init(configuration:ReadConfiguration)throws{bytes=configuration.file.regularFileContents ?? Data()}
    func fileWrapper(configuration:WriteConfiguration)throws->FileWrapper{FileWrapper(regularFileWithContents:bytes)}
}
@main struct ShijiApp:App {
    @StateObject var library=MobileLibrary()
    @StateObject var sync=ComputerSync()
    @Environment(\.scenePhase) var phase
    var body:some Scene {WindowGroup{RootView().environmentObject(library).environmentObject(sync).tint(Color("AccentColor")).task{sync.activate(library)}.onReceive(library.$resources){sync.changed($0)}.onOpenURL{sync.openPairing($0)}.onChange(of:phase){_,value in if value == .active{library.reload();sync.activate(library)}else{sync.deactivate()}}}}
}
struct RootView:View {
    @AppStorage("shiji-v2-appearance") var appearance="dark"
    @AppStorage("shiji-v2-motion-mode") var motionMode="studio"
    @SceneStorage("shiji-v2-intro-shown") var introShown=false
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @Environment(\.scenePhase) var scenePhase
    @State var introVisible=false
    @State var introTask:Task<Void,Never>?

    @EnvironmentObject var library:MobileLibrary
    @EnvironmentObject var sync:ComputerSync
    var body:some View {
        TabView {
            NavigationStack{GalleryView()}.tabItem{Label("资源库",systemImage:"square.grid.2x2")}
            NavigationStack{ProjectsView()}.tabItem{Label("集合",systemImage:"folder")}
            NavigationStack{SettingsView()}.tabItem{Label("管理",systemImage:"slider.horizontal.3")}
        }.overlay{if introVisible{NativeMotionIntro().id(library.introSequence).allowsHitTesting(false).accessibilityHidden(true)}}
            .overlay(alignment:.bottomTrailing){if introVisible{Button("跳过开场"){stopIntro()}.padding(16).background(Color(uiColor:NativePalette.raised),in:Capsule()).padding(24)}}
            .task{if !introShown{introShown=true;library.introSequence+=1}}
            .onChange(of:library.introSequence){_,_ in playIntro()}
            .onChange(of:motionMode){_,_ in if motionMode=="calm"{stopIntro()}}
            .onChange(of:reduceMotion){_,value in if value{stopIntro()}}
            .onChange(of:scenePhase){_,value in if value != .active{stopIntro()}}
            .onDisappear{stopIntro()}
            .preferredColorScheme(appearance=="system" ? nil : appearance=="light" ? .light : .dark).sheet(isPresented:$sync.pairingOpen){NavigationStack{ComputerSyncView().toolbar{ToolbarItem(placement:.cancellationAction){Button("完成"){sync.pairingOpen=false}.disabled(sync.busy)}}}}
            .alert("暂时无法完成",isPresented:Binding(get:{library.error != nil},set:{if !$0{library.error=nil}})){Button("知道了",role:.cancel){library.error=nil}}message:{Text(library.error ?? "")}
            .alert("已完成",isPresented:Binding(get:{library.notice != nil},set:{if !$0{library.notice=nil}})){Button("好",role:.cancel){library.notice=nil}}message:{Text(library.notice ?? "")}
    }
    func stopIntro(){introTask?.cancel();introVisible=false}
    func playIntro(){stopIntro();guard !reduceMotion,motionMode=="studio",scenePhase == .active else{return};introVisible=true;introTask=Task{try? await Task.sleep(nanoseconds:1_450_000_000);if !Task.isCancelled{introVisible=false}}}
}
struct GalleryView:View {
    @EnvironmentObject var library:MobileLibrary
    @AppStorage("shiji-v2-motion-mode") var motionMode="studio"
    @State var captureVisible=false
    @State var stamp:String?
    @State var stampID=UUID()
    @State var stampTask:Task<Void,Never>?
    @State var captureTask:Task<Void,Never>?
    @State var search=""
    @State var category="全部"
    @State var scope="全部"
    @State var editor=false
    @State var filesOpen=false
    @State var expanded=false
    @Namespace var namespace
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @Environment(\.dynamicTypeSize) var typeSize
    let categories=["全部","UI / 设计","美术素材","音频","视频","字体","3D","灵感","开发工具","其他"]
    var active:[Resource]{library.resources.filter{!$0.flag("deleted")}}
    var filtered:[Resource]{library.resources.filter{!$0.flag("deleted") && (category=="全部" || $0.text("category")==category) && (scope != "常用" || $0.flag("favorite")) && (scope != "待整理" || $0.flag("inbox")) && (search.isEmpty || [$0.title,$0.text("description"),$0.text("notes"),$0.names("tags").joined(separator:" ")].joined(separator:" ").localizedCaseInsensitiveContains(search))}}
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:20){
                if search.isEmpty && category=="全部" && scope=="全部" && !typeSize.isAccessibilitySize {
                    NativeBrandHero(calm:reduceMotion || motionMode=="calm",replay:{library.introSequence+=1})
                }

                ScrollView(.horizontal){HStack(spacing:8){ForEach(categories,id:\.self){name in Button{nameButton(name)}label:{Text(name).font(.subheadline.weight(.medium)).padding(.horizontal,16).frame(minHeight:44).background(category==name ? Color.accentColor : Color(uiColor:NativePalette.raised),in:Capsule()).foregroundStyle(category==name ? Color(uiColor:NativePalette.onAccent) : Color.primary)}.buttonStyle(.plain).accessibilityAddTraits(category==name ? .isSelected : [])}}}.scrollIndicators(.hidden)
                HStack(alignment:.firstTextBaseline){
                    Text("\(filtered.count) 条收藏").font(.subheadline).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
                    Spacer()
                    if category != "全部" || scope != "全部"{Button("清除筛选",systemImage:"xmark.circle"){category="全部";scope="全部"}.font(.subheadline).frame(minHeight:44)}
                }
                if filtered.isEmpty {
                    if typeSize.isAccessibilitySize {
                        VStack(alignment:.leading,spacing:12){
                            Text(active.isEmpty ? "留给下一次创作" : "没有匹配的收藏").font(.title2.weight(.semibold))
                            Text(active.isEmpty ? "收藏一个网址、添加素材，或连接电脑同步已有收藏。" : "试试其他关键词，或清除分类和浏览范围。").foregroundStyle(Color(uiColor:NativePalette.secondaryText))
                        }.padding(.vertical,8)
                    }else{
                        ContentUnavailableView(active.isEmpty ? "留给下一次创作" : "没有匹配的收藏",systemImage:active.isEmpty ? "bookmark" : "magnifyingglass",description:Text(active.isEmpty ? "收藏一个网址、添加素材，或连接电脑同步已有收藏。" : "试试其他关键词，或清除分类和浏览范围。"))
                    }
                    if active.isEmpty {
                        Button("收藏第一个资源",systemImage:"plus"){editor=true}.buttonStyle(.borderedProminent).foregroundStyle(Color(uiColor:NativePalette.onAccent)).controlSize(.large).frame(maxWidth:.infinity,minHeight:44)
                        NavigationLink{ComputerSyncView()}label:{Label("连接电脑",systemImage:"desktopcomputer").frame(maxWidth:.infinity,minHeight:44)}
                    }else{Button("清除搜索与筛选"){search="";category="全部";scope="全部"}.frame(maxWidth:.infinity,minHeight:44)}
                } else {LazyVStack(spacing:28){ForEach(filtered){resource in resourceLink(resource).modifier(NativeMotionReveal()).transition(.asymmetric(insertion:.move(edge:.bottom).combined(with:.opacity),removal:.scale(scale:0.79).combined(with:.opacity)))}}}
            }.padding(.horizontal,20).padding(.top,10).padding(.bottom,24)
        }.scrollDismissesKeyboard(.interactively).background(Color(uiColor:NativePalette.background)).navigationTitle("拾集 SHIJI®")
            .searchable(text:$search,prompt:"搜索资源、标签与灵感")
            .toolbar{ToolbarItem(placement:.topBarLeading){NavigationLink{ComputerSyncView()}label:{Image(systemName:"desktopcomputer").frame(width:44,height:44)}.accessibilityLabel("电脑同步")};ToolbarItem(placement:.topBarTrailing){Menu{Picker("浏览范围",selection:$scope){ForEach(["全部","常用","待整理"],id:\.self){Text($0)}}}label:{Label(scope,systemImage:"line.3.horizontal.decrease")}}}
            .safeAreaInset(edge:.bottom,alignment:.trailing){if !active.isEmpty{captureDock.padding(.horizontal,20).padding(.bottom,10)}}
            .overlay{if let stamp,!reduceMotion,motionMode=="studio"{ZStack{NativeMotionBurst(count:6);Text(stamp).font(.title.weight(.black)).italic().padding(24).background(Color.accentColor).foregroundStyle(Color(uiColor:NativePalette.onAccent)).rotationEffect(.degrees(-4))}.id(stampID).allowsHitTesting(false).accessibilityHidden(true).transition(.scale(scale:1.4).combined(with:.opacity))}}
            .overlay(alignment:.top){if captureVisible{ZStack{if !reduceMotion,motionMode=="studio"{NativeMotionBurst(count:15).frame(width:160,height:160);NativeSavedFlight().id(library.captureSequence)};Label("已收藏到拾集",systemImage:"checkmark.circle.fill").font(.subheadline.weight(.semibold)).padding(14).background(Color.accentColor,in:Capsule()).foregroundStyle(Color(uiColor:NativePalette.onAccent)).padding(.top,8).transition(.move(edge:.top).combined(with:.opacity))}}}
            .animation(reduceMotion || motionMode=="calm" ? nil : .spring(response:0.35,dampingFraction:0.85),value:captureVisible)
            .onChange(of:library.captureSequence){_,_ in
                captureTask?.cancel();captureVisible=true
                UIAccessibility.post(notification:.announcement,argument:"已收藏到拾集")
                captureTask=Task{try? await Task.sleep(nanoseconds:1_600_000_000);if !Task.isCancelled{captureVisible=false}}
            }
            .onChange(of:category){_,value in showStamp(value)}
            .onChange(of:scope){_,value in showStamp(value)}
            .onChange(of:motionMode){_,value in if value=="calm"{stampTask?.cancel();stamp=nil}}
            .onChange(of:reduceMotion){_,value in if value{stampTask?.cancel();stamp=nil}}
            .onDisappear{captureTask?.cancel();captureVisible=false;stampTask?.cancel();stamp=nil}
            .sheet(isPresented:$editor){EditorView(resource:nil)}
            .fileImporter(isPresented:$filesOpen,allowedContentTypes:[.image,.audio,.movie,.pdf,.plainText],allowsMultipleSelection:false){result in if case .success(let urls)=result,let url=urls.first{Task{await library.addFile(url)}}else if case .failure(let error)=result{library.error=error.localizedDescription}}
    }
    @ViewBuilder private func resourceLink(_ resource:Resource)->some View {
        if #available(iOS 18,*),!reduceMotion && motionMode=="studio" {
            NavigationLink{DetailView(id:resource.id).navigationTransition(.zoom(sourceID:resource.id,in:namespace))}label:{ResourceCard(resource:resource).matchedTransitionSource(id:resource.id,in:namespace)}.buttonStyle(.plain)
        }else{NavigationLink{DetailView(id:resource.id)}label:{ResourceCard(resource:resource)}.buttonStyle(.plain)}
    }
    func showStamp(_ label:String){stampTask?.cancel();guard !reduceMotion,motionMode=="studio" else{stamp=nil;return};stampID=UUID();withAnimation(.easeOut(duration:0.18)){stamp=label};stampTask=Task{try? await Task.sleep(nanoseconds:650_000_000);if !Task.isCancelled{withAnimation(.easeOut(duration:0.25)){stamp=nil}}}}
    func nameButton(_ name:String){withAnimation(reduceMotion || motionMode=="calm" ? nil : .spring(response:0.35,dampingFraction:0.9)){category=name}}
    @ViewBuilder var captureDock:some View {
        if typeSize.isAccessibilitySize {
            captureMenu
        } else if #available(iOS 26,*) {
            ViewThatFits(in:.horizontal){GlassEffectContainer(spacing:14){HStack(spacing:10){
                if expanded {
                    Button{editor=true;expanded=false}label:{Label("网址",systemImage:"link").fixedSize(horizontal:true,vertical:false).padding(.horizontal,18).frame(minHeight:48)}.buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("add",in:namespace)
                    Button{filesOpen=true;expanded=false}label:{Label("素材",systemImage:"square.and.arrow.down").fixedSize(horizontal:true,vertical:false).padding(.horizontal,18).frame(minHeight:48)}.buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("files",in:namespace)
                    Button{toggle()}label:{Image(systemName:"xmark").frame(width:48,height:48)}.buttonStyle(.plain).glassEffect(.regular.interactive(),in:.circle).accessibilityLabel("收起收藏")
                }else{Button{toggle()}label:{Label("收藏",systemImage:"plus").padding(.horizontal,20).frame(minHeight:48)}.buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("add",in:namespace)}
            }.font(.body.weight(.semibold)).fixedSize(horizontal:true,vertical:false)};captureMenu}
        }else{captureMenu}
    }
    var captureMenu:some View {Menu{Button("收藏网址",systemImage:"link"){editor=true};Button("添加素材",systemImage:"square.and.arrow.down"){filesOpen=true}}label:{Label("收藏",systemImage:"plus").fixedSize(horizontal:true,vertical:false).padding(16).background(.regularMaterial,in:Capsule())}}
    func toggle(){withAnimation(reduceMotion || motionMode=="calm" ? nil : .spring(response:0.38,dampingFraction:0.82)){expanded.toggle()}}
}
struct ResourceCard:View {
    @EnvironmentObject var library:MobileLibrary
    var resource:Resource
    var body:some View {
        VStack(alignment:.leading,spacing:12){LocalCover(resource:resource).frame(height:coverHeight).clipShape(RoundedRectangle(cornerRadius:14))
            Text(resource.presentation=="tool" ? "TOOL / 开发工具" : resource.presentation=="text" ? "TEXT / 灵感笔记" : "VISUAL / 视觉素材").font(.caption2.weight(.semibold)).tracking(1).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
            HStack(alignment:.top){Text(resource.title).font(.title3.weight(.semibold)).foregroundStyle(.primary).multilineTextAlignment(.leading);Spacer();if resource.flag("favorite"){Image(systemName:"star.fill").foregroundStyle(Color.accentColor).accessibilityLabel("常用资源")}}
            ViewThatFits(in:.horizontal){HStack{Text(source).lineLimit(1);Spacer();Text(resource.text("category"))};VStack(alignment:.leading,spacing:4){Text(source).lineLimit(2);Text(resource.text("category"))}}.font(.caption).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
            if !resource.text("description").isEmpty{Text(resource.text("description")).font(.subheadline).foregroundStyle(Color(uiColor:NativePalette.secondaryText)).lineLimit(2).multilineTextAlignment(.leading)}
            if !resource.attachments.isEmpty{Label("\(resource.attachments.count) 个附件",systemImage:"paperclip").font(.caption).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
        }.contentShape(Rectangle()).accessibilityElement(children:.combine)
    }
    private var source:String{URL(string:resource.text("url"))?.host ?? "本机素材"}
    private var coverHeight:CGFloat{let cover=resource.text("coverId");let images=resource.attachments.filter{($0["mime"] as? String ?? "").hasPrefix("image/")};return images.contains{library.files?.file($0["id"] as? String ?? "") != nil} || !cover.isEmpty && library.files?.file(cover) != nil ? 220 : 142}
}
struct LocalCover:View {
    @EnvironmentObject var library:MobileLibrary
    var resource:Resource
    var cover:String {resource.text("coverId").isEmpty ? resource.attachments.first(where:{($0["mime"] as? String ?? "").hasPrefix("image/")})?["id"] as? String ?? "" : resource.text("coverId")}
    var body:some View {
        GeometryReader { bounds in
            Group {
                if let url=library.files?.file(cover),let image=LocalImage.image(url:url){Image(uiImage:image).resizable().scaledToFill()}
                else if resource.presentation=="text",!resource.text("snippet").isEmpty{ZStack(alignment:.topLeading){Color(uiColor:NativePalette.raised);Text(resource.text("snippet").prefix(240)).font(.system(.body,design:.monospaced)).foregroundStyle(Color.purple).padding(22)}}
                else{ZStack{Color(uiColor:NativePalette.raised);VStack(spacing:12){Image(systemName:resource.presentation=="tool" ? "curlybraces" : resource.text("kind")=="file" ? "doc.richtext" : "link").font(.largeTitle).foregroundStyle(Color.accentColor);Text(URL(string:resource.text("url"))?.host ?? resource.text("category")).font(.headline).foregroundStyle(Color(uiColor:NativePalette.secondaryText)).lineLimit(2).padding(.horizontal,20)}}}
            }.frame(width:bounds.size.width,height:bounds.size.height).clipped().accessibilityHidden(true)
        }
    }
}
struct DetailView:View {
    @EnvironmentObject var library:MobileLibrary
    @Environment(\.dismiss) var dismiss
    let id:String
    @State var editor=false
    @State var deleteConfirm=false
    @State var filePicker=false
    @State var previewURL:URL?
    @State var favoriteMoment=false
    @State var favoriteTask:Task<Void,Never>?
    @AppStorage("shiji-v2-motion-mode") var motionMode="studio"
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    var resource:Resource? {library.resources.first{$0.id==id}}
    var body:some View {
        Group{if let r=resource {
            ScrollView{VStack(alignment:.leading,spacing:24){
                LocalCover(resource:r).frame(height:240).clipped().clipShape(RoundedRectangle(cornerRadius:14))
                VStack(alignment:.leading,spacing:8){Text(r.title).font(.title2.weight(.semibold));Text((URL(string:r.text("url"))?.host ?? "本机素材")+" · "+String(r.text("createdAt").prefix(10))).font(.subheadline).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}.modifier(NativeMotionReveal(delay:0.12))
                if let url=URL(string:r.text("url")),["http","https"].contains(url.scheme ?? ""){Link("打开原网页",destination:url).frame(minHeight:44)}
                if !r.text("description").isEmpty{Text(r.text("description")).modifier(NativeMotionReveal(delay:0.26))}
                VStack(alignment:.leading,spacing:12){Text("来源与授权").font(.headline);Text(r.text("author").isEmpty ? "作者待补充" : r.text("author")).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
                    Text(r.text("license").isEmpty ? "待确认" : r.text("license")).font(.subheadline.weight(.medium)).padding(8).background((r.text("license").isEmpty || r.text("license")=="待确认") ? Color.yellow.opacity(0.2) : Color(uiColor:.tertiarySystemFill),in:Capsule())
                    if let url=URL(string:r.text("sourceUrl")),["http","https"].contains(url.scheme ?? ""){Link("查看来源",destination:url).frame(minHeight:44)}
                    if let url=URL(string:r.text("licenseUrl")),["http","https"].contains(url.scheme ?? ""){Link("查看授权说明",destination:url).frame(minHeight:44)}
                }
                if !r.names("tags").isEmpty{Text(r.names("tags").joined(separator:" · ")).font(.subheadline).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
                if !r.names("projects").isEmpty{Text("项目："+r.names("projects").joined(separator:" · ")).font(.subheadline)}
                if !r.text("notes").isEmpty{VStack(alignment:.leading,spacing:12){Text("收藏备注").font(.headline);Text(r.text("notes")).textSelection(.enabled)}}
                VStack(alignment:.leading,spacing:12){HStack{Text("附件").font(.headline);Spacer();Button("添加",systemImage:"plus"){filePicker=true}.frame(minHeight:44)};ForEach(r.attachments.indices,id:\.self){i in let a=r.attachments[i];Button{openAttachment(a)}label:{HStack{Image(systemName:"doc");Text(a["name"] as? String ?? "附件").lineLimit(2);Spacer();Image(systemName:"chevron.right")}.frame(minHeight:44)}.buttonStyle(.plain)}}
            }.padding(20)}.background(Color(uiColor:NativePalette.background)).navigationTitle(r.title).navigationBarTitleDisplayMode(.inline)
                .toolbar{ToolbarItem(placement:.topBarTrailing){Menu{Button(r.flag("favorite") ? "取消常用" : "设为常用",systemImage:"star"){if library.change(id,"favorite",!r.flag("favorite")),!r.flag("favorite"),!reduceMotion,motionMode=="studio"{favoriteTask?.cancel();favoriteMoment=true;favoriteTask=Task{try? await Task.sleep(nanoseconds:850_000_000);if !Task.isCancelled{favoriteMoment=false}}}};Button(r.flag("inbox") ? "标为已整理" : "放入待整理",systemImage:"tray"){library.change(id,"inbox",!r.flag("inbox"))};Button("移到回收站",systemImage:"trash",role:.destructive){deleteConfirm=true}}label:{Image(systemName:"ellipsis").frame(width:44,height:44)}}}
                .safeAreaInset(edge:.bottom){Button("编辑",systemImage:"pencil"){editor=true}.buttonStyle(.borderedProminent).foregroundStyle(Color(uiColor:NativePalette.onAccent)).controlSize(.large).frame(maxWidth:.infinity).padding(16).background(.bar)}
                .sheet(isPresented:$editor){EditorView(resource:r)}
                .confirmationDialog("移到回收站？可在管理页恢复。",isPresented:$deleteConfirm,titleVisibility:.visible){Button("移到回收站",role:.destructive){library.change(id,"deleted",true);dismiss()}}
                .fileImporter(isPresented:$filePicker,allowedContentTypes:[.image,.audio,.movie,.pdf,.plainText]){result in switch result{case .success(let url):Task{await library.addFile(url,id:id)};case .failure(let e):library.error=e.localizedDescription}}
                .overlay{if favoriteMoment{NativeMotionBurst(count:6).allowsHitTesting(false).accessibilityHidden(true)}}
                .onChange(of:reduceMotion){_,value in if value{favoriteMoment=false}}
                .onChange(of:motionMode){_,value in if value=="calm"{favoriteMoment=false}}
                .onDisappear{favoriteTask?.cancel();favoriteMoment=false}
                .quickLookPreview($previewURL)
        }else{ContentUnavailableView("资源暂时不可用",systemImage:"doc")}}
    }
    func openAttachment(_ a:[String:Any]){library.perform{
        guard let id=a["id"] as? String,let source=library.files?.file(id)else{throw fail("附件缺失，请从有效备份重新导入。")}
        let ext=URL(fileURLWithPath:a["name"] as? String ?? "file").pathExtension.filter{$0.isLetter || $0.isNumber}.prefix(12)
        let directory=FileManager.default.temporaryDirectory.appendingPathComponent("ShijiPreviews",isDirectory:true)
        try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        let old=try FileManager.default.contentsOfDirectory(at:directory,includingPropertiesForKeys:nil)
        for file in old{try? FileManager.default.removeItem(at:file)}
        let target=directory.appendingPathComponent(id+(ext.isEmpty ? "" : "."+ext))
        try FileManager.default.copyItem(at:source,to:target);previewURL=target
    }}
}
struct EditorView:View {
    @EnvironmentObject var library:MobileLibrary
    @Environment(\.dismiss) var dismiss
    var resource:Resource?
    @State var quickMode=true
    @State var title=""
    @State var url=""
    @State var category="其他"
    @State var kind="website"
    @State var notes=""
    @State var description=""
    @State var author=""
    @State var license="待确认"
    @State var licenseURL=""
    @State var sourceURL=""
    @State var tags=[String]()
    @State var tag=""
    @State var projects=[String]()
    @State var project=""
    @State var confirmDiscard=false
    @State var initialized=false
    @State var original:Resource?
    @State var saveError:String?
    var draft:[String:Any]{var raw=original?.raw ?? LibraryFiles.newRecord(title:title,url:url,kind:kind);for (key,value) in ["title":title,"url":url,"category":category,"kind":kind,"notes":notes,"description":description,"author":author,"license":license,"licenseUrl":licenseURL,"sourceUrl":sourceURL]{raw[key]=value};raw["tags"]=tags;raw["projects"]=projects;raw["collection"]=projects.first ?? "";return raw}
    var changed:Bool{if let r=original{return title != r.title || url != r.text("url") || notes != r.text("notes") || category != r.text("category") || kind != r.text("kind") || description != r.text("description") || author != r.text("author") || license != r.text("license") || licenseURL != r.text("licenseUrl") || sourceURL != r.text("sourceUrl") || tags != r.names("tags") || projects != r.names("projects") || !tag.isEmpty || !project.isEmpty};return !title.isEmpty || !url.isEmpty || !notes.isEmpty || !description.isEmpty || !author.isEmpty || !sourceURL.isEmpty || !licenseURL.isEmpty || license != "待确认" || category != "其他" || kind != "website" || !tags.isEmpty || !tag.isEmpty || !projects.isEmpty || !project.isEmpty}
    var body:some View {
        NavigationStack{Form{
            if quickMode {
                Section("拾起一个好链接"){
                    TextField("https://…",text:$url).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled().submitLabel(.done)
                    Text("先保存到这部 iPhone，离线也能收藏。名称会使用网站域名或仓库路径，之后可以编辑。").font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
                    Button("完整编辑 / 代码与提示词"){quickMode=false}
                }
            } else {
            Section("资源"){TextField("名称",text:$title);Picker("形式",selection:$kind){Text("网站").tag("website");Text("素材").tag("file");Text("代码").tag("code");Text("提示词").tag("prompt")};TextField("网址",text:$url).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled();Picker("类型",selection:$category){ForEach(["开发工具","美术素材","UI / 设计","音频","视频","字体","3D","灵感","其他"],id:\.self){Text($0)}};TextField("介绍",text:$description,axis:.vertical)}
            Section("标签"){ForEach(tags,id:\.self){name in HStack{Text(name);Spacer();Button{tags.removeAll{$0==name}}label:{Image(systemName:"xmark.circle").frame(width:44,height:44)}.buttonStyle(.borderless).accessibilityLabel("移除标签 "+name)}};TextField("输入完整名称，按回车确认",text:$tag).submitLabel(.done).onSubmit{commitTag()};Text("逗号可以是标签名称的一部分。").font(.caption).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
            Section("项目"){ForEach(projects,id:\.self){name in HStack{Text(name);Spacer();Button{projects.removeAll{$0==name}}label:{Image(systemName:"xmark.circle").frame(width:44,height:44)}.buttonStyle(.borderless).accessibilityLabel("移出项目 "+name)}};TextField("输入项目，按回车确认",text:$project).submitLabel(.done).onSubmit{commitProject()}}
            Section("收藏备注"){TextEditor(text:$notes).frame(minHeight:120)}
            Section("来源与授权"){TextField("作者",text:$author);TextField("来源网址",text:$sourceURL).keyboardType(.URL).textInputAutocapitalization(.never);Picker("授权",selection:$license){ForEach(Array(Set(["待确认","允许商用","需署名","仅个人使用",license])).sorted(),id:\.self){Text($0)}};TextField("授权说明网址",text:$licenseURL).keyboardType(.URL).textInputAutocapitalization(.never)}
            }
        }.navigationTitle(resource==nil ? "收藏资源" : "编辑资源").navigationBarTitleDisplayMode(.inline)
            .toolbar{ToolbarItem(placement:.cancellationAction){Button("取消"){if changed{confirmDiscard=true}else{dismiss()}}.keyboardShortcut(.cancelAction)};ToolbarItem(placement:.confirmationAction){Button("保存"){commitTag();commitProject();do{guard let files=library.files else{throw fail("收藏库不可用，请检查共享目录配置。")};let value:[String:Any]
                if quickMode {let normalized=try LibraryFiles.normalize(url);guard !normalized.isEmpty else{throw fail("请输入有效的网址。")};value=LibraryFiles.newRecord(title:LibraryFiles.quickTitle(normalized),url:normalized,kind:"website")}else{value=draft}
                try files.save(value,expected:original?.raw);library.reload();if original==nil{library.captureSequence+=1};dismiss()}catch{saveError=error.localizedDescription}}.keyboardShortcut("s",modifiers:.command).disabled(quickMode ? url.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty : title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)}}
            .interactiveDismissDisabled(changed)
            .alert("未能保存",isPresented:Binding(get:{saveError != nil},set:{if !$0{saveError=nil}})){Button("继续编辑",role:.cancel){saveError=nil}}message:{Text(saveError ?? "")}
            .confirmationDialog("放弃未保存的修改？",isPresented:$confirmDiscard,titleVisibility:.visible){Button("放弃修改",role:.destructive){dismiss()};Button("继续编辑",role:.cancel){}}
            .onDisappear{library.editing=false}
            .onAppear{library.editing=true;guard !initialized else{return};initialized=true;original=resource;quickMode=resource==nil;if let r=original{title=r.title;url=r.text("url");category=r.text("category");kind=r.text("kind");notes=r.text("notes");description=r.text("description");author=r.text("author");license=r.text("license");licenseURL=r.text("licenseUrl");sourceURL=r.text("sourceUrl");tags=r.names("tags");projects=r.names("projects")}}
        }
    }
    func commitTag(){let name=tag.trimmingCharacters(in:.whitespacesAndNewlines);if !name.isEmpty,!tags.contains(name){tags.append(name)};tag=""}
    func commitProject(){let name=project.trimmingCharacters(in:.whitespacesAndNewlines);if !name.isEmpty,!projects.contains(name){projects.append(name)};project=""}
}
struct ProjectsView:View {
    @EnvironmentObject var library:MobileLibrary
    var names:[String]{Array(Set(library.resources.filter{!$0.flag("deleted")}.flatMap{$0.names("projects")})).sorted()}
    var body:some View{List{if names.isEmpty{ContentUnavailableView("按项目归拢灵感",systemImage:"folder",description:Text("在资源编辑页添加项目，同一项目的收藏会出现在这里。"))}else{ForEach(names,id:\.self){name in NavigationLink{ProjectResources(name:name)}label:{Label(name,systemImage:"folder")}}}}.navigationTitle("集合")}
}
struct ProjectResources:View{
    @EnvironmentObject var library:MobileLibrary
    let name:String
    var body:some View{ScrollView{LazyVStack(spacing:24){ForEach(library.resources.filter{!$0.flag("deleted") && $0.names("projects").contains(name)}){r in NavigationLink{DetailView(id:r.id)}label:{ResourceCard(resource:r)}.buttonStyle(.plain)}}.padding(20)}.background(Color(uiColor:.systemGroupedBackground)).navigationTitle(name)}
}
struct SettingsView:View {
    @AppStorage("shiji-v2-appearance") var appearance="dark"
    @AppStorage("shiji-v2-motion-mode") var motionMode="studio"


    @EnvironmentObject var library:MobileLibrary
    @EnvironmentObject var sync:ComputerSync
    @State var importer=false
    @State var exporter=false
    @State var document=BackupDocument(Data())
    @State var plan:ImportPlan?
    @State var previewOpen=false
    var body:some View {
        List{
            Section {
                LabeledContent("本机收藏",value:"\(library.resources.filter{!$0.flag("deleted")}.count) 条")
                NavigationLink{ComputerSyncView()}label:{Label{VStack(alignment:.leading,spacing:5){Text("电脑同步");Text(syncSummary).font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}}icon:{Image(systemName:"desktopcomputer")}}
            } header:{Text("收藏与同步")}footer:{Text("收藏保存在这部 iPhone，无需账号，可离线使用。") }
            Section("外观与动效"){
                Picker("外观",selection:$appearance){Text("Creative Tech 深色").tag("dark");Text("浅色").tag("light");Text("跟随系统").tag("system")}
                Picker("动效",selection:$motionMode){Text("Motion Studio").tag("studio");Text("Calm").tag("calm")}
                Text("系统“减少动态效果”优先于 Motion Studio。外观偏好不会改变收藏或同步内容。").font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
            }
            Section("导入与备份"){Button("导入电脑备份",systemImage:"square.and.arrow.down"){importer=true}.disabled(library.busy);Button("导出完整备份",systemImage:"square.and.arrow.up"){Task{if let bytes=await library.export(){document=BackupDocument(bytes);exporter=true}}}.disabled(library.busy);if library.busy{ProgressView("正在处理文件…")};Text("支持拾集 JSON 和完整 ZIP；JSON 不含附件。ZIP 导入前会校验，确认后只加入新收藏，不覆盖已有资源。").font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
            Section{NavigationLink("回收站"){TrashView()}}
            Section("快速收藏"){Text("在 Safari、照片或其他 App 点分享，选择“拾集”。也可以在资源库点击收藏，添加网址或本机素材。");Text("若分享列表暂时没有拾集，请在“更多”里启用。若仍未出现，请确认已安装完整 App。").font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
        }.navigationTitle("管理")
            .fileImporter(isPresented:$importer,allowedContentTypes:[.json,.zip]){result in switch result{case .success(let url):Task{if let p=await library.preview(url){plan=p;previewOpen=true}};case .failure(let e):library.error=e.localizedDescription}}
            .sheet(isPresented:$previewOpen){NavigationStack{List{Section("导入摘要"){LabeledContent("备份资源",value:"\(plan?.resources.count ?? 0) 条");LabeledContent("附件",value:"\(plan?.fileCount ?? 0) 个");Text("只加入尚未收藏的资源；已存在的名称、备注、标签和附件全部保留。");if plan?.files.isEmpty==true{Text("该文件不含本地附件，导入后可能没有封面。")}}}.navigationTitle("确认导入").toolbar{ToolbarItem(placement:.cancellationAction){Button("取消"){previewOpen=false;plan=nil}};ToolbarItem(placement:.confirmationAction){Button("加入资源"){if let p=plan{previewOpen=false;plan=nil;Task{await library.merge(p)}}}}}}}
            .fileExporter(isPresented:$exporter,document:document,contentType:.zip,defaultFilename:"Shiji-iPhone-backup"){result in if case .failure(let e)=result{library.error=e.localizedDescription}}
    }
    private var syncSummary:String{if sync.busy{return "正在同步…"};if let pending=sync.pending{return "\(pending.plan.conflicts.count) 条资源需要选择版本"};if sync.problem != nil{return "同步需要重试"};return sync.connection?.computerName ?? "尚未配对 · 同一 Wi-Fi 同步"}

}
struct TrashView:View {
    @EnvironmentObject var library:MobileLibrary
    var body:some View{List{let deleted=library.resources.filter{$0.flag("deleted")};if deleted.isEmpty{ContentUnavailableView("回收站是空的",systemImage:"trash")}else{ForEach(deleted){r in HStack{Text(r.title);Spacer();Button("恢复"){library.change(r.id,"deleted",false)}.frame(minHeight:44)}}}}.navigationTitle("回收站")}
}

struct NativeBookmark:Shape {
    func path(in r:CGRect)->Path {Path { p in
        p.move(to:CGPoint(x:r.minX,y:r.minY));p.addLine(to:CGPoint(x:r.maxX,y:r.minY));p.addLine(to:CGPoint(x:r.maxX,y:r.maxY));p.addLine(to:CGPoint(x:r.midX,y:r.height*0.72));p.addLine(to:CGPoint(x:r.minX,y:r.maxY));p.closeSubpath()
    }}
}
struct NativeBrandHero:View {
    let calm:Bool
    let replay:()->Void
    @Environment(\.scenePhase) var phase
    @State private var visible=false
    @State private var epoch=Date()
    private let lime=Color(red:215/255,green:1,blue:101/255)
    private let violet=Color(red:165/255,green:140/255,blue:1)
    var body:some View {
        VStack(alignment:.leading,spacing:20){
            (Text("好灵感，\n")+Text("值得拾起。").foregroundColor(Color.accentColor)).font(.largeTitle.weight(.black)).tracking(-1).modifier(NativeMotionReveal())
            Text("把散落各处的灵感，收进你的创作宇宙。").font(.subheadline).foregroundStyle(Color(uiColor:NativePalette.secondaryText))
            TimelineView(.animation(minimumInterval:1/30,paused:calm || phase != .active || !visible)){context in
                let t=calm ? 0 : context.date.timeIntervalSince(epoch)
                GeometryReader{bounds in
                    ZStack(alignment:.bottomLeading){
                        violet
                        Ellipse().stroke(.black.opacity(0.15),style:StrokeStyle(lineWidth:1,dash:[4,4])).padding(15).rotationEffect(.degrees(t*20))
                        Ellipse().stroke(.black.opacity(0.15),lineWidth:1).frame(width:bounds.size.width*1.8,height:180).rotationEffect(.degrees(-30+sin(t/4)*35)).offset(x:35,y:-12)
                        RoundedRectangle(cornerRadius:CGFloat(20+sin(t)*16)).stroke(lime,lineWidth:12).frame(width:56,height:56).rotationEffect(.degrees(t*38)).scaleEffect(0.9+sin(t)*0.1).offset(x:25,y:-60)
                        Image(systemName:"sparkle").font(.system(size:28,weight:.bold)).foregroundStyle(lime).scaleEffect(1+sin(t*1.5)*0.2).rotationEffect(.degrees(sin(t)*20)).offset(x:55,y:-135)
                        NativeBookmark().fill(lime).frame(width:90,height:128).overlay{NativeBookmark().fill(Color(red:12/255,green:13/255,blue:16/255)).frame(width:45,height:94)}.rotationEffect(.degrees(-22+sin(t)*5)).offset(x:bounds.size.width*0.51,y:-30+sin(t)*12)
                        Text("KEEP IDEAS.").font(.largeTitle.weight(.black)).tracking(-1).foregroundStyle(.black).padding(20)
                    }
                }
            }.frame(height:190).clipShape(RoundedRectangle(cornerRadius:16)).accessibilityHidden(true)
                .background{GeometryReader{proxy in Color.clear.preference(key:NativeHeroVisibility.self,value:proxy.frame(in:.global).intersects(UIScreen.main.bounds))}}
                .onPreferenceChange(NativeHeroVisibility.self){visible=$0}
            Button("重播品牌开场",systemImage:"arrow.clockwise",action:replay).font(.caption.weight(.semibold)).frame(minHeight:44).disabled(calm)
        }.onAppear{visible=true;epoch=Date()}.onDisappear{visible=false}
    }
}
struct NativeMotionReveal:ViewModifier {
    var delay:Double=0
    @AppStorage("shiji-v2-motion-mode") var mode="studio"
    @Environment(\.accessibilityReduceMotion) var reduce
    @State private var entered=false
    func body(content:Content)->some View {
        let moving = !reduce && mode=="studio" && !entered
        content.opacity(moving ? 0.2 : 1).offset(y:moving ? 28 : 0).blur(radius:moving ? 6 : 0)
            .onAppear{withAnimation(reduce || mode=="calm" ? nil : .timingCurve(0.16,1,0.24,1,duration:0.85).delay(delay)){entered=true}}
    }
}
struct NativeCurtain:Shape {
    var progress:Double
    var animatableData:Double{get{progress}set{progress=newValue}}
    func path(in rect:CGRect)->Path {let height=progress<0.21 ? progress/0.21 : progress<0.65 ? 1 : max(0,(1-progress)/0.35);return Path(CGRect(x:0,y:0,width:rect.width,height:rect.height*height))}
}
struct NativeMotionIntro:View {
    @State private var progress=0.0
    var body:some View {
        ZStack{Color(red:215/255,green:1,blue:101/255);VStack(spacing:14){(Text("SHIJI")+Text("®").foregroundColor(Color(red:131/255,green:92/255,blue:244/255))).font(.system(size:85,weight:.black)).tracking(-3).rotationEffect(.degrees(-6));Text("KEEP WHAT MOVES YOU.").font(.caption.weight(.bold)).tracking(1)}}.foregroundStyle(Color(red:12/255,green:13/255,blue:16/255)).clipShape(NativeCurtain(progress:progress)).ignoresSafeArea().onAppear{withAnimation(.timingCurve(0.65,0,0.25,1,duration:1.37)){progress=1}}
    }
}
struct NativeMotionBurst:View {
    var count=6
    @State private var expanded=false
    private let colors=[Color(red:215/255,green:1,blue:101/255),Color(red:165/255,green:140/255,blue:1),Color(red:121/255,green:223/255,blue:1),Color(red:1,green:157/255,blue:135/255)]
    var body:some View {ZStack{Circle().stroke(colors[0],lineWidth:2).frame(width:30,height:30).scaleEffect(expanded ? 5.2 : 0.2).opacity(expanded ? 0 : 0.95);ForEach(0..<count,id:\.self){i in let angle=Double(i)*Double.pi*2/Double(count);RoundedRectangle(cornerRadius:i%4==0 ? 4 : 1).fill(colors[i%4]).frame(width:8,height:8).rotationEffect(.degrees(expanded ? Double(i)*36 : 0)).offset(x:expanded ? cos(angle)*80 : 0,y:expanded ? sin(angle)*80 : 0).opacity(expanded ? 0 : 1)}}.frame(width:180,height:180).onAppear{withAnimation(.timingCurve(0.18,1,0.4,1,duration:0.85)){expanded=true}}}
}

struct NativeHeroVisibility:PreferenceKey {static var defaultValue=false;static func reduce(value:inout Bool,nextValue:()->Bool){value=nextValue()}}
struct NativeSavedFlight:View {
    @State private var progress:CGFloat=0
    var body:some View{NativeBookmark().fill(Color.accentColor).frame(width:32,height:42).modifier(NativeFlightPath(progress:progress)).onAppear{withAnimation(.timingCurve(0.25,0.84,0.28,1,duration:0.9)){progress=1}}}
}
struct NativeFlightPath:AnimatableModifier {
    var progress:CGFloat
    var animatableData:CGFloat{get{progress}set{progress=newValue}}
    func body(content:Content)->some View{content.offset(x:sin(progress * .pi)*40,y:(1-progress)*150).rotationEffect(.degrees(Double(progress)*210-15)).scaleEffect(max(0.1,1-progress*0.9)).opacity(progress>0.8 ? Double((1-progress)*5) : 1)}
}
