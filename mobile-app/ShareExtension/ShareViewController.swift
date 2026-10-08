import UIKit
import OSLog
import SwiftUI
import UniformTypeIdentifiers
final class ShareViewController:UIViewController {
    private let trace=Logger(subsystem:"local.silver.shiji.mobile.share",category:"lifecycle")
    private var url="",note="",attachment:(Data,String,String)?
    private var host:UIHostingController<ShareForm>?
    override func viewDidLoad(){super.viewDidLoad();trace.info("Share controller view loaded");show(loading:true);Task{await readProviders()}}
    private func show(loading:Bool,error:String?=nil){trace.info("Rendering share form, loading=\(loading), failure=\(error != nil)");let form=ShareForm(url:url,note:note,loading:loading,error:error,save:{[weak self] title,note in try self?.save(title:title,note:note)},cancel:{[weak self] in self?.extensionContext?.completeRequest(returningItems:nil)})
        if let host{host.rootView=form}else{let controller=UIHostingController(rootView:form);host=controller;addChild(controller);view.addSubview(controller.view);controller.view.translatesAutoresizingMaskIntoConstraints=false;NSLayoutConstraint.activate([controller.view.leadingAnchor.constraint(equalTo:view.leadingAnchor),controller.view.trailingAnchor.constraint(equalTo:view.trailingAnchor),controller.view.topAnchor.constraint(equalTo:view.topAnchor),controller.view.bottomAnchor.constraint(equalTo:view.bottomAnchor)]);controller.didMove(toParent:self)}}
    override func viewDidAppear(_ animated:Bool){super.viewDidAppear(animated);trace.info("Share controller appeared, width=\(self.view.bounds.width), height=\(self.view.bounds.height), children=\(self.children.count)")}
    private func object(_ p:NSItemProvider,_ type:String) async throws -> NSSecureCoding {try await withCheckedThrowingContinuation{continuation in p.loadItem(forTypeIdentifier:type,options:nil){value,error in if let error{continuation.resume(throwing:error)}else if let value{continuation.resume(returning:value)}else{continuation.resume(throwing:fail("无法读取分享内容。"))}}}}
    private func readProviders() async {
        do {let providers=(extensionContext?.inputItems as? [NSExtensionItem] ?? []).flatMap{$0.attachments ?? []};guard !providers.isEmpty else{throw fail("没有可收藏的内容。")}
            trace.info("Reading share providers, count=\(providers.count)");for p in providers.prefix(8) {
                if p.hasItemConformingToTypeIdentifier(UTType.url.identifier),let value=try await object(p,UTType.url.identifier) as? URL,["https","http"].contains(value.scheme ?? ""){url=value.absoluteString}
                else if p.hasItemConformingToTypeIdentifier(UTType.image.identifier),attachment==nil {let value=try await object(p,UTType.image.identifier);var bytes:Data?;if let u=value as? URL{let size=try u.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0;guard size<=PortableZIP.maxFile else{throw fail("分享的图片超过 64 MB。")};bytes=try Data(contentsOf:u)}else if let d=value as? Data{bytes=d}else if let image=value as? UIImage{bytes=image.pngData()};guard let bytes,bytes.count<=PortableZIP.maxFile,let image=LocalImage.image(data:bytes),let jpeg=image.jpegData(compressionQuality:0.9)else{throw fail("图片无法读取或超过上限。")};attachment=(jpeg,"分享的图片.jpg","image/jpeg")}
                else if p.hasItemConformingToTypeIdentifier(UTType.plainText.identifier),let text=try await object(p,UTType.plainText.identifier) as? String{if url.isEmpty,(try? LibraryFiles.normalize(text)) != nil,text.hasPrefix("http"){url=text}else{note=String((note+"\n"+text).trimmingCharacters(in:.whitespacesAndNewlines).prefix(10000))}}
            };guard !url.isEmpty || !note.isEmpty || attachment != nil else{throw fail("当前分享内容不支持收藏，请分享网址、文字或图片。")};show(loading:false)
        }catch{show(loading:false,error:error.localizedDescription)}
    }
    private func save(title:String,note:String) throws{let files=try LibraryFiles(root:LibraryFiles.appRoot());try files.capture(url:url,title:title,text:note,attachment:attachment);extensionContext?.completeRequest(returningItems:nil)}
}
struct ShareForm:View {
    let url:String,note:String,loading:Bool,error:String?,save:(String,String)throws->Void,cancel:()->Void
    @State private var saveError:String?
    @State private var title=""
    @State private var draftNote=""
    var body:some View{NavigationStack{Form{if loading{ProgressView("正在读取分享内容…")}else{if let problem=saveError ?? error{Section{Text(problem).foregroundStyle(.red)}};Section("收藏到拾集"){TextField("名称（可选）",text:$title);if !url.isEmpty{Text(url).font(.footnote).foregroundStyle(.secondary)};TextField("收藏备注",text:$draftNote,axis:.vertical)};Text("内容保存在本机，回到拾集即可查看。已有网址会保留原名称和标签，并加入新备注。").font(.footnote).foregroundStyle(.secondary)}}.navigationTitle("收藏到拾集").navigationBarTitleDisplayMode(.inline).toolbar{ToolbarItem(placement:.cancellationAction){Button("取消",action:cancel).keyboardShortcut(.cancelAction)};ToolbarItem(placement:.confirmationAction){Button("保存"){do{try save(title,draftNote);saveError=nil}catch{saveError=error.localizedDescription}}.keyboardShortcut("s",modifiers:.command).disabled(loading || error != nil)}}.onChange(of:note,initial:true){_,value in draftNote=value}}}
}
