import SwiftUI
import UIKit

@MainActor final class ComputerSync:ObservableObject {
    @Published var connection:SyncConnection?
    @Published var busy=false
    @Published var message="连接同一 Wi-Fi，和电脑同步收藏。"
    @Published var problem:String?
    @Published var lastSuccess:Date?
    @Published var pending:PreparedSync?
    @Published var choices=[String:String]()
    @Published var pairingCode=""
    @Published var pairingOpen=false
    @Published var automatic=UserDefaults.standard.object(forKey:"sync.foreground-auto") as? Bool ?? true {
        didSet{UserDefaults.standard.set(automatic,forKey:"sync.foreground-auto");if active{startTimer()}}
    }
    private var library:MobileLibrary?
    private var active=false
    private var timer:Task<Void,Never>?,scheduled:Task<Void,Never>?
    private var seen:Data?
    init(){do{connection=try SyncCredentials.load();if let id=connection?.libraryID{lastSuccess=UserDefaults.standard.object(forKey:"sync.lastSuccess."+id) as? Date}}catch{problem=error.localizedDescription}}
    private var checkpointURL:URL?{library?.files?.root.appendingPathComponent("sync-checkpoint.json")}
    private func base() throws -> [Resource] {
        guard let path=checkpointURL,FileManager.default.fileExists(atPath:path.path)else{return []}
        let raw=try JSONSerialization.jsonObject(with:Data(contentsOf:path)) as? [String:Any] ?? [:]
        let snapshot=try SyncSnapshot(raw);guard snapshot.libraryID==connection?.libraryID else{throw fail("同步记录属于另一资源库。请解除配对后重新连接。")};return snapshot.resources
    }
    func activate(_ library:MobileLibrary){self.library=library;active=true;startTimer();schedule()}
    func deactivate(){active=false;timer?.cancel();scheduled?.cancel()}
    func changed(_ resources:[Resource]){let value=try? SyncMerge.fullSnapshot(resources);guard value != seen else{return};seen=value;schedule()}
    private func schedule(){guard active,automatic,connection != nil,!busy,pending==nil else{return};scheduled?.cancel();scheduled=Task{try? await Task.sleep(nanoseconds:2_000_000_000);guard !Task.isCancelled else{return};await synchronize()}}
    private func startTimer(){timer?.cancel();guard active,automatic,connection != nil else{return};timer=Task{while !Task.isCancelled{try? await Task.sleep(nanoseconds:30_000_000_000);guard !Task.isCancelled else{return};if pending==nil{await synchronize()}}}}
    func pair() async {guard !busy else{return};busy=true;problem=nil;defer{busy=false;schedule()}
        do{let parsed=try SyncConnection.parse(pairingCode);let paired=try await SyncExchange.pair(parsed,name:UIDevice.current.name);try SyncCredentials.save(paired)
            if connection?.libraryID != paired.libraryID,let checkpointURL{try? FileManager.default.removeItem(at:checkpointURL)}
            if connection?.libraryID != paired.libraryID{lastSuccess=UserDefaults.standard.object(forKey:"sync.lastSuccess."+paired.libraryID) as? Date};connection=paired;pairingCode="";pending=nil;choices=[:];message="配对成功，可以同步收藏。";startTimer()
        }catch{problem=error.localizedDescription}
    }
    func synchronize() async {guard !busy,let connection,let files=library?.files,library?.busy != true,library?.editing != true else{return};busy=true;problem=nil;message="正在比较两端收藏…";defer{busy=false}
        do{let prepared=try await SyncExchange.prepare(connection,files:files,base:base());if !prepared.plan.conflicts.isEmpty{pending=prepared;choices=[:];message="有 \(prepared.plan.conflicts.count) 条资源需要选择版本。";return};try await finish(prepared,files:files,connection:connection)
        }catch{problem=readable(error);message="收藏保留在本机，可以稍后重试。";library?.reload()}
    }
    func resolve() async {guard !busy,let prepared=pending,prepared.plan.conflicts.allSatisfy({["phone","computer"].contains(choices[$0.id] ?? "")}),let files=library?.files,let connection else{return};busy=true;problem=nil;message="正在同步所选版本…";defer{busy=false}
        do{try await finish(prepared,files:files,connection:connection)}catch{problem=readable(error);pending=nil;choices=[:];message="两端内容可能已变化，请重新同步并比较。";library?.reload()}
    }
    private func finish(_ prepared:PreparedSync,files:LibraryFiles,connection:SyncConnection) async throws {
        message="正在传输收藏与素材…"
        let result=try await SyncExchange.commit(prepared,connection:connection,files:files,choices:choices)
        if let checkpointURL{let bytes=try JSONSerialization.data(withJSONObject:result.metadata,options:.sortedKeys);try bytes.write(to:checkpointURL,options:[.atomic,.completeFileProtectionUntilFirstUserAuthentication])}
        pending=nil;choices=[:];seen=try SyncMerge.fullSnapshot(result.resources);library?.reload();lastSuccess=Date();UserDefaults.standard.set(lastSuccess,forKey:"sync.lastSuccess."+connection.libraryID);message="两端收藏已同步。"
    }
    func forget(){guard !busy else{return};do{try SyncCredentials.forget();if let id=connection?.libraryID{UserDefaults.standard.removeObject(forKey:"sync.lastSuccess."+id)};if let checkpointURL{try? FileManager.default.removeItem(at:checkpointURL)};connection=nil;pending=nil;choices=[:];pairingCode="";lastSuccess=nil;problem=nil;message="已断开连接，收藏仍保留在本机。";timer?.cancel();scheduled?.cancel()}catch{problem=error.localizedDescription}}
    func openPairing(_ url:URL){guard url.scheme=="shiji-sync",url.host=="pair",!busy else{return};pairingCode=url.absoluteString;pairingOpen=true}
    private func readable(_ error:Error)->String {let e=error as NSError;if e.domain==NSURLErrorDomain{return "暂时无法连接电脑。请确认两端在同一 Wi-Fi、电脑已开启同步，并允许拾集访问本地网络。证书变化时需要重新配对。"};return error.localizedDescription}
}
struct ComputerSyncView:View {
    @EnvironmentObject var sync:ComputerSync
    @State private var disconnect=false
    @FocusState private var codeFocused:Bool
    private var secondary:Color{Color(uiColor:NativePalette.secondaryText)}
    private var selectedCount:Int{sync.pending?.plan.conflicts.filter{["phone","computer"].contains(sync.choices[$0.id] ?? "")}.count ?? 0}
    var body:some View {
        Form {
            Section {
                VStack(alignment:.leading,spacing:12){
                    Text(sync.connection?.computerName ?? "把电脑里的灵感带在身边").font(.headline).fixedSize(horizontal:false,vertical:true).frame(maxWidth:.infinity,alignment:.leading)
                    if sync.busy{HStack(spacing:10){ProgressView();Text(sync.message)}}
                    else{Label(status,systemImage:statusSymbol).font(.subheadline).foregroundStyle(secondary)}
                    if let date=sync.lastSuccess{Text("上次同步 "+date.formatted(date:.abbreviated,time:.shortened)).font(.footnote).foregroundStyle(secondary)}
                }.padding(.vertical,8)
            } footer: {if sync.connection==nil{Text("无需账号。两端连接同一 Wi-Fi，配对后同步收藏与素材。")}}
            if let error=sync.problem {
                Section("需要处理") {Label{Text(error).textSelection(.enabled)}icon:{Image(systemName:"exclamationmark.triangle")}.foregroundStyle(.primary)}
            }
            if sync.connection==nil {
                Section("连接电脑") {
                    Label("电脑端打开“手机同步”，开启服务并生成配对码。",systemImage:"desktopcomputer").foregroundStyle(secondary)
                    Label("用 iPhone 相机扫二维码，或复制配对码后粘贴。",systemImage:"qrcode.viewfinder").foregroundStyle(secondary)
                    SecureField("粘贴电脑配对码",text:$sync.pairingCode).textInputAutocapitalization(.never).autocorrectionDisabled().focused($codeFocused).submitLabel(.done).onSubmit{codeFocused=false}.disabled(sync.busy)
                    PasteButton(payloadType:String.self){values in if let first=values.first{sync.pairingCode=first;codeFocused=false}}.disabled(sync.busy)
                }
                Section {
                    Button{codeFocused=false;Task{await sync.pair()}}label:{Label(sync.busy ? "正在配对…" : "配对这台电脑",systemImage:"link").frame(maxWidth:.infinity,minHeight:44)}
                        .buttonStyle(.borderedProminent).foregroundStyle(Color(uiColor:NativePalette.onAccent)).disabled(sync.busy || sync.pairingCode.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
                } footer:{Text("配对码五分钟内有效，只使用一次。")}
            } else {
                if let pending=sync.pending {
                    Section {
                        HStack{Text("已选择 \(selectedCount) / \(pending.plan.conflicts.count)").font(.subheadline.weight(.medium));Spacer()}
                        ForEach(pending.plan.conflicts){conflict in
                            NavigationLink{SyncConflictView(conflict:conflict)}label:{VStack(alignment:.leading,spacing:6){Text(conflict.title).font(.body.weight(.medium));Label(sync.choices[conflict.id].map{$0=="phone" ? "保留手机版本" : "保留电脑版本"} ?? "比较并选择版本",systemImage:sync.choices[conflict.id]==nil ? "square.on.square" : "checkmark.circle").font(.footnote).foregroundStyle(secondary)}}.disabled(sync.busy)
                        }
                        Button{Task{await sync.resolve()}}label:{Text("同步所选版本").frame(maxWidth:.infinity,minHeight:44)}.buttonStyle(.borderedProminent).foregroundStyle(Color(uiColor:NativePalette.onAccent)).disabled(sync.busy || selectedCount != pending.plan.conflicts.count)
                    } header:{Text("选择保留的版本")}footer:{Text("两端的修改需要比较。逐条选择后再同步；选择本身不会写入收藏。")}
                }else{
                    Section {Button{Task{await sync.synchronize()}}label:{Label(sync.problem==nil ? "立即同步" : "重新同步",systemImage:"arrow.triangle.2.circlepath").frame(maxWidth:.infinity,minHeight:44)}.buttonStyle(.borderedProminent).foregroundStyle(Color(uiColor:NativePalette.onAccent)).disabled(sync.busy)}
                }
                Section {
                    Toggle("App 前台自动同步",isOn:$sync.automatic).disabled(sync.busy)
                } header:{Text("同步方式")}footer:{Text("打开 App 或修改收藏后同步。后台暂停；离线时可以继续收藏。")}
                Section {Button("断开这台电脑",role:.destructive){disconnect=true}.frame(minHeight:44).disabled(sync.busy)}header:{Text("连接管理")}footer:{Text("断开仅清除手机的配对与同步记录，收藏和素材保留。")}
            }
            Section {
                DisclosureGroup("会同步哪些内容") {Text("资源名称、网址、备注、标签、项目归属、来源授权、常用和待整理状态、回收站与附件。项目层级和智能集合由电脑管理。电脑需保持运行并开启同步。").font(.footnote).foregroundStyle(secondary)}
            }
        }.navigationTitle("电脑同步").navigationBarTitleDisplayMode(.inline)
            .confirmationDialog("断开电脑？本机收藏会保留。",isPresented:$disconnect,titleVisibility:.visible){Button("断开连接",role:.destructive){sync.forget()}}
    }
    private var status:String {
        if sync.pending != nil{return "有资源需要选择版本"}
        if sync.problem != nil{return "暂时未同步，收藏保留在本机"}
        if sync.connection==nil{return "同一 Wi-Fi · 双向同步"}
        return sync.lastSuccess==nil ? "已配对，等待首次同步" : "已配对"
    }
    private var statusSymbol:String{sync.pending != nil ? "square.on.square" : sync.problem != nil ? "exclamationmark.circle" : sync.connection==nil ? "wifi" : "link"}
}
struct SyncConflictView:View {
    @EnvironmentObject var sync:ComputerSync
    let conflict:SyncConflict
    var body:some View {Form {
        Section {Text(conflict.title).font(.headline);if conflict.identityCollision{Text("两端分别收藏了同一网址。请选择完整版本，合并到电脑已有记录。").foregroundStyle(Color(uiColor:NativePalette.secondaryText))};Text("选择整个资源版本，包括备注、标签、授权与附件归属。未选择的版本不会自动覆盖。缺失版本将按回收站状态处理。").font(.footnote).foregroundStyle(Color(uiColor:NativePalette.secondaryText))}
        Section("本次选择") {Picker("使用版本",selection:Binding(get:{sync.choices[conflict.id] ?? ""},set:{if $0.isEmpty{sync.choices.removeValue(forKey:conflict.id)}else{sync.choices[conflict.id]=$0}})){Text("尚未选择").tag("");Text("手机版本").tag("phone");Text("电脑版本").tag("computer")}.pickerStyle(.inline).disabled(sync.busy)}
        version("手机",conflict.phone)
        version("电脑",conflict.computer)
    }.navigationTitle("比较版本").navigationBarTitleDisplayMode(.inline)}
    @ViewBuilder func version(_ label:String,_ r:Resource?)->some View {
        Section(label+"版本") {if let r {
            LabeledContent("状态",value:r.flag("deleted") ? "回收站" : "收藏库")
            ForEach([("title","名称"),("url","网址"),("description","介绍"),("notes","备注"),("category","分类"),("kind","形式"),("author","作者"),("license","授权"),("sourceUrl","来源"),("licenseUrl","授权说明"),("price","价格"),("snippet","文本内容")],id:\.0){key,name in if !r.text(key).isEmpty{VStack(alignment:.leading,spacing:6){Text(name).font(.caption).foregroundStyle(Color(uiColor:NativePalette.secondaryText));Text(r.text(key)).textSelection(.enabled)}}}
            Text("标签："+r.names("tags").joined(separator:" · "));Text("项目："+r.names("projects").joined(separator:" · "))
            Text("附件：\(r.attachments.count) 个");ForEach(r.attachments.indices,id:\.self){index in Text(r.attachments[index]["name"] as? String ?? "素材")};if !r.text("coverId").isEmpty{Text("封面："+(r.attachments.first{$0["id"] as? String==r.text("coverId") }?["name"] as? String ?? "已设置"))};if let notes=r.raw["projectNotes"] as? [String:String]{ForEach(notes.keys.sorted(),id:\.self){name in Text(name+"："+(notes[name] ?? ""))}};if !r.names("colors").isEmpty{Text("色彩："+r.names("colors").joined(separator:" · "))};Text(r.flag("favorite") ? "已设为常用" : "未设为常用");Text(r.flag("inbox") ? "待整理" : "已整理")
        }else{Text("此端已移除记录。选择此版本会将另一端记录放入回收站，保留素材文件。")}}
    }
}
