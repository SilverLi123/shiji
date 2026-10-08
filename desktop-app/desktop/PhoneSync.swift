import SwiftUI
import AppKit
import CoreImage.CIFilterBuiltins

@MainActor final class PhoneSyncModel:ObservableObject {
    let base:URL
    @Published var enabled=false
    @Published var busy=false
    @Published var addresses=[String]()
    @Published var address=""
    @Published var devices=[String]()
    @Published var code=""
    @Published var expires:Date?
    @Published var error:String?
    @Published var copied=false
    @Published var certificateRenewed=false
    private var stateRevision=0
    private var failedAction:String?
    init(base:URL){self.base=base}
    func request(_ action:String?=nil,body:[String:Any]=[:]) async throws -> [String:Any] {
        var request=URLRequest(url:base.appendingPathComponent("api/mobile-sync"+(action.map{"/"+$0} ?? "")));request.timeoutInterval=15
        if action != nil{request.httpMethod="POST";request.setValue("application/json",forHTTPHeaderField:"Content-Type");request.httpBody=try JSONSerialization.data(withJSONObject:body)}
        let(data,response)=try await URLSession.shared.data(for:request)
        guard let json=try JSONSerialization.jsonObject(with:data) as? [String:Any],(response as? HTTPURLResponse)?.statusCode==200 else{throw NSError(domain:"ShijiSync",code:1,userInfo:[NSLocalizedDescriptionKey:"无法连接电脑同步服务。检查网络、端口或重新打开 App。"])}
        return json
    }
    func update(_ value:[String:Any]){enabled=value["enabled"] as? Bool ?? false;certificateRenewed=value["certificateRenewed"] as? Bool ?? false;if value["pairingAvailable"] as? Bool==false{code="";expires=nil;copied=false};addresses=value["addresses"] as? [String] ?? [];if !addresses.contains(address){address=addresses.first ?? ""};devices=(value["devices"] as? [[String:Any]] ?? []).compactMap{$0["name"] as? String}}
    func perform(_ action:String?=nil) async {guard !busy else{return};busy=true;stateRevision+=1;error=nil;failedAction=nil;defer{busy=false}
        do{let result=try await request(action);update(result);if action=="stop" || action=="revoke"{code="";expires=nil;copied=false}}catch{failedAction=action ?? "status";self.error=readable(error)}}
    func makeCode() async {guard !busy else{return};busy=true;stateRevision+=1;error=nil;failedAction=nil;defer{busy=false}
        do{let result=try await request("pair",body:["address":address]);code=result["code"] as? String ?? "";expires=Date().addingTimeInterval(300);copied=false}catch{failedAction="pair";self.error=readable(error)}}
    func refresh() async {guard !busy else{return};let expected=stateRevision;do{let value=try await request();guard !busy,stateRevision==expected else{return};update(value)
        if failedAction=="status" || failedAction=="enable" && enabled || failedAction=="stop" && !enabled || failedAction=="revoke" && devices.isEmpty{error=nil;failedAction=nil}
    }catch{if !busy,stateRevision==expected{failedAction="status";self.error=readable(error)}}}
    private func readable(_ error:Error)->String {let value=error as NSError;if value.domain==NSURLErrorDomain{return value.code==NSURLErrorTimedOut ? "连接本机服务超时，请重试。" : "暂时无法连接本机服务，请确认 App 正在运行。"};return error.localizedDescription}
    func copy(){guard !code.isEmpty else{return};NSPasteboard.general.clearContents();NSPasteboard.general.setString(code,forType:.string);copied=true}
    var qr:NSImage? {guard !code.isEmpty else{return nil};let filter=CIFilter.qrCodeGenerator();filter.message=Data(code.utf8);filter.correctionLevel="M";guard let output=filter.outputImage,let cg=CIContext().createCGImage(output.transformed(by:CGAffineTransform(scaleX:5,y:5)),from:output.extent.applying(CGAffineTransform(scaleX:5,y:5)))else{return nil};return NSImage(cgImage:cg,size:NSSize(width:220,height:220))}
}
struct PhoneSyncPanel:View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var model:PhoneSyncModel
    @State private var revoke=false
    init(baseURL:URL){_model=StateObject(wrappedValue:PhoneSyncModel(base:baseURL))}
    private var supportingText:Color{Color(nsColor:.labelColor).opacity(0.78)}
    var body:some View {
        VStack(alignment:.leading,spacing:0){
            VStack(alignment:.leading,spacing:8){
                Text("手机与电脑同步").font(.title2.weight(.semibold))
                Text("同一 Wi-Fi 下，让收藏和素材在两端接上。").foregroundStyle(supportingText)
            }.padding(24)
            Divider()
            ScrollView {
                VStack(alignment:.leading,spacing:24){
                    HStack(alignment:.center,spacing:16){
                        VStack(alignment:.leading,spacing:7){Label(model.enabled ? "同步服务已开启" : "同步服务未开启",systemImage:model.enabled ? "checkmark.shield" : "pause.circle").font(.headline);Text(model.enabled ? "保持 App 运行，手机即可发起同步。" : "开启后，在 iPhone 配对这台电脑。").foregroundStyle(supportingText)}
                        Spacer()
                        if !model.enabled{Button("开启同步"){Task{await model.perform("enable")}}.buttonStyle(.borderedProminent).controlSize(.large).disabled(model.busy)}
                    }
                    if let error=model.error{Label(error,systemImage:"exclamationmark.triangle").textSelection(.enabled)}
                    if model.enabled {
                        if model.certificateRenewed && !model.devices.isEmpty{Label("电脑地址或证书已更新，请在手机断开后重新配对。收藏会保留。",systemImage:"exclamationmark.circle")}
                        VStack(alignment:.leading,spacing:12){
                            Text("连接 iPhone").font(.headline)
                            if model.addresses.count>1{Picker("电脑地址",selection:$model.address){ForEach(model.addresses,id:\.self){Text($0=="127.0.0.1" ? "127.0.0.1（仅本机）" : $0).tag($0)}}.disabled(model.busy).onChange(of:model.address){_,_ in model.code="";model.expires=nil}}
                            if model.address=="127.0.0.1"{Text("当前只有本机地址。连接 Wi-Fi 后停止并重新开启同步，再选择 Wi-Fi 地址。").foregroundStyle(supportingText)}
                            if let qr=model.qr,let expiry=model.expires {
                                HStack(alignment:.top,spacing:24){
                                    Image(nsImage:qr).interpolation(.none).resizable().frame(width:260,height:260).padding(12).background(.white).accessibilityLabel("手机同步配对二维码")
                                    VStack(alignment:.leading,spacing:16){
                                        Text("用 iPhone 系统相机扫码，在拾集确认配对。")
                                        Text("也可以复制配对码，在手机“管理 → 电脑同步”中粘贴。").foregroundStyle(supportingText)
                                        TimelineView(.periodic(from:.now,by:1)){context in
                                            Button(model.copied ? "已复制" : "复制配对码",systemImage:model.copied ? "checkmark" : "doc.on.doc",action:model.copy).disabled(model.busy || context.date>=expiry)
                                            Text(context.date<expiry ? "五分钟内有效，仅使用一次。" : "已过期，请生成新码。").font(.caption).foregroundStyle(supportingText)
                                        }
                                    }
                                }
                            }
                            Button(model.code.isEmpty ? "生成配对码" : "生成新配对码",systemImage:"qrcode"){Task{await model.makeCode()}}.controlSize(.large).disabled(model.busy || model.address.isEmpty || model.address=="127.0.0.1")
                            Text("配对码只交给自己的手机。").font(.caption).foregroundStyle(supportingText)
                        }
                        if !model.devices.isEmpty{
                            Divider()
                            VStack(alignment:.leading,spacing:12){Text("已配对的手机").font(.headline);ForEach(Array(model.devices.enumerated()),id:\.offset){_,name in Label(name,systemImage:"iphone")};Button("解除所有手机配对",role:.destructive){revoke=true}.disabled(model.busy)}
                        }
                    }
                    Text("iPhone 可在 App 前台自动同步。两端都改过的资源，会在手机让你选择保留的版本。").font(.callout).foregroundStyle(supportingText)
                }.frame(maxWidth:.infinity,alignment:.leading).padding(24)
            }
            Divider()
            HStack(spacing:16){
                if model.enabled{Button("停止同步"){Task{await model.perform("stop")}}.disabled(model.busy).help("停止服务，保留收藏和已配对手机。")}
                if model.busy{ProgressView().controlSize(.small);Text("正在连接…").font(.caption).foregroundStyle(supportingText)}
                Spacer()
                Button("完成"){dismiss()}.keyboardShortcut(.cancelAction)
            }.padding(20)
        }.frame(width:640,height:!model.enabled ? 320 : model.code.isEmpty ? 480 : 710).tint(Color(red:0.196,green:0.353,blue:0.290))
            .task{await model.perform();while !Task.isCancelled{try? await Task.sleep(nanoseconds:5_000_000_000);guard !Task.isCancelled else{return};await model.refresh()}}
            .confirmationDialog("解除所有手机配对？收藏会保留。",isPresented:$revoke,titleVisibility:.visible){Button("解除配对",role:.destructive){Task{await model.perform("revoke")}}}
    }
}
