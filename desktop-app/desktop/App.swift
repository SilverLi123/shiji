import SwiftUI
import WebKit
import AppKit

@MainActor final class LibraryRuntime: ObservableObject {
    @Published var ready = false
    @Published var controlsBlocked = false
    @Published var motionCalm = false
    @Published var error: String?
    @Published var pageError: String?
    @Published var pairing = ""
    @Published var pairingError: String?
    @Published var pairingLoading = false
    let port = Int(ProcessInfo.processInfo.environment["SHIJI_PORT"] ?? "8782") ?? 8782
    let instance = UUID().uuidString
    var process: Process?
    var check: Task<Void, Never>?
    var webView: WKWebView?
    var base: URL { URL(string: "http://127.0.0.1:\(port)")! }
    var dataDirectory: URL {
        if let value = ProcessInfo.processInfo.environment["SHIJI_DATA_DIR"] { return URL(fileURLWithPath: value) }
        return FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("DevResourceLibrary")
    }
    lazy var diagnostics = RuntimeDiagnostics(root: dataDirectory)
    func start() {
        diagnostics.record("service.start-request", ["owned": process != nil])
        guard process == nil else { return }
        ready = false; error = nil
        guard let resources = Bundle.main.resourceURL else { error = "App 文件不完整，请重新构建。"; return }
        let candidates = [ProcessInfo.processInfo.environment["SHIJI_PYTHON"], "/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3"].compactMap { $0 }
        guard let python = candidates.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else { error = "需要 Python 3.9 或更新版本，请安装后重试。"; return }
        let child = Process(); child.executableURL = URL(fileURLWithPath: python)
        child.arguments = [resources.appendingPathComponent("backend/desktop_service.py").path, "--port", String(port), "--data-dir", dataDirectory.path, "--instance", instance]
        var environment = ProcessInfo.processInfo.environment; environment["PYTHONUNBUFFERED"] = "1"; child.environment = environment
        let log = dataDirectory.appendingPathComponent("desktop.log")
        do {
            try FileManager.default.createDirectory(at: dataDirectory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            if !FileManager.default.fileExists(atPath: log.path) { FileManager.default.createFile(atPath: log.path, contents: nil) }
            let handle = try FileHandle(forWritingTo: log); try handle.truncate(atOffset: 0); child.standardOutput = handle; child.standardError = handle
            child.terminationHandler = { [weak self] _ in Task { @MainActor in
                guard let self else { return }; self.diagnostics.record("service.exit"); self.ready = false; self.process = nil
                if self.error == nil { self.error = "本地服务已停止。请重试，或打开日志检查端口与数据目录。" }
            } }
            try child.run(); process = child; diagnostics.record("service.spawn", ["pid": child.processIdentifier])
        } catch { self.error = "无法启动服务：\(error.localizedDescription)"; return }
        check = Task { [weak self] in
            guard let self else { return }
            for _ in 0..<80 {
                guard !Task.isCancelled, self.process?.isRunning == true else { return }
                var request = URLRequest(url: self.base.appendingPathComponent("api/desktop-status")); request.timeoutInterval = 1
                if let (data, _) = try? await URLSession.shared.data(for: request),
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any], json["instance"] as? String == self.instance {
                    self.diagnostics.record("service.ready"); self.ready = true; await self.readPairing(); return
                }
                try? await Task.sleep(nanoseconds: 250_000_000)
            }
            self.error = "服务启动超时。检查端口 \(self.port) 是否占用，或打开日志查看原因。"; self.stop()
        }
    }
    func readPairing() async {
        guard !pairingLoading else { return }
        pairingLoading = true; pairingError = nil
        defer { pairingLoading = false }
        do {
            var request = URLRequest(url:base.appendingPathComponent("api/pairing")); request.timeoutInterval = 5
            let (data, response) = try await URLSession.shared.data(for:request)
            guard (response as? HTTPURLResponse)?.statusCode == 200,
                  let json = try JSONSerialization.jsonObject(with:data) as? [String:String],
                  let token = json["token"], !token.isEmpty else { throw URLError(.badServerResponse) }
            pairing = token
        } catch { pairing = ""; pairingError = "暂时无法读取配对码，请重试。" }
    }
    func command(_ name: String, value: String = "") {
        guard ready, let view = webView, view.url?.host == "127.0.0.1", view.url?.port == port else { return }
        let data = try! JSONSerialization.data(withJSONObject: ["name":name,"value":value]); let json = String(data:data,encoding:.utf8)!
        view.evaluateJavaScript("window.ShijiDesktop?.command(\(json))", completionHandler: nil)
    }
    func stop() { diagnostics.record("service.stop"); check?.cancel(); if process?.isRunning == true { process?.terminate() } }
    func retryPage() {
        guard ready, process?.isRunning == true, let view=webView else { start(); return }
        diagnostics.record("webview.user-retry"); pageError=nil
        view.load(URLRequest(url:URL(string:base.absoluteString+"/?desktop=1")!))
    }
    func copyPairing() { guard !pairing.isEmpty else { return }; NSPasteboard.general.clearContents(); NSPasteboard.general.setString(pairing, forType: .string) }
    func revealExtension() {
        guard let folder = Bundle.main.resourceURL?.appendingPathComponent("browser-extension") else { return }
        NSWorkspace.shared.activateFileViewerSelecting([folder])
    }
}

struct ManagementView: NSViewRepresentable {
    @ObservedObject var runtime: LibraryRuntime
    func makeCoordinator() -> Coordinator { Coordinator(runtime) }
    func makeNSView(context: Context) -> WKWebView {
        runtime.diagnostics.record("webview.create", ["appActive": NSApp.isActive])
        let config = WKWebViewConfiguration()
        config.userContentController.addUserScript(WKUserScript(source:"window.ShijiNative=true;",injectionTime:.atDocumentStart,forMainFrameOnly:true))
        config.userContentController.add(context.coordinator,name:"libraryState")
        config.userContentController.add(context.coordinator,name:"libraryMotion")
        config.userContentController.add(context.coordinator,name:"libraryDiagnostics")
        if ProcessInfo.processInfo.environment["SHIJI_QA_METRICS"] == "1",
           let file = Bundle.main.resourceURL?.appendingPathComponent("backend/static/runtime-diagnostics.js"),
           let script = try? String(contentsOf:file,encoding:.utf8) {
            config.userContentController.addUserScript(WKUserScript(source:script,injectionTime:.atDocumentStart,forMainFrameOnly:true))
        }
        config.userContentController.addUserScript(WKUserScript(source:"""
        (()=>{let previous;const update=()=>{const drawer=document.querySelector('#drawer');const busy=!!document.querySelector('dialog[open]')||!!(drawer&&!drawer.hidden);if(busy!==previous){previous=busy;window.webkit.messageHandlers.libraryState.postMessage(busy)}};new MutationObserver(update).observe(document.body,{subtree:true,attributes:true,attributeFilter:['hidden','open']});update()})();
        """,injectionTime:.atDocumentEnd,forMainFrameOnly:true))
        config.userContentController.addUserScript(WKUserScript(source:"""
        /* shiji-motion-bridge */
        (()=>{let previous;const update=()=>{const mode=document.documentElement.dataset.shijiMotion==='calm'?'calm':'studio';if(mode!==previous){previous=mode;window.webkit.messageHandlers.libraryMotion.postMessage(mode)}};new MutationObserver(update).observe(document.documentElement,{attributes:true,attributeFilter:['data-shiji-motion']});update()})();
        /* end-shiji-motion-bridge */
        """,injectionTime:.atDocumentEnd,forMainFrameOnly:true))
        let view = WKWebView(frame:.zero,configuration:config); view.navigationDelegate=context.coordinator; view.uiDelegate=context.coordinator
        view.setValue(false,forKey:"drawsBackground"); view.setContentHuggingPriority(.defaultLow,for:.horizontal); view.setContentHuggingPriority(.defaultLow,for:.vertical); runtime.webView=view
        context.coordinator.observeLifecycle(view)
        view.load(URLRequest(url:URL(string:runtime.base.absoluteString+"/?desktop=1")!)); return view
    }
    func updateNSView(_ view: WKWebView, context: Context) {}
    static func dismantleNSView(_ view: WKWebView, coordinator: Coordinator) {
        coordinator.runtime.diagnostics.record("webview.dismantle")
        for name in ["libraryState","libraryMotion","libraryDiagnostics"] { view.configuration.userContentController.removeScriptMessageHandler(forName:name) }
        view.navigationDelegate=nil; view.uiDelegate=nil
        if coordinator.runtime.webView === view { coordinator.runtime.webView=nil }
    }
    class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate, WKScriptMessageHandler {
        let runtime: LibraryRuntime
        var observations: [NSObjectProtocol] = []
        init(_ runtime: LibraryRuntime) { self.runtime=runtime }
        func observeLifecycle(_ view: WKWebView) {
            for name in [NSApplication.didBecomeActiveNotification, NSApplication.didResignActiveNotification, NSWindow.didBecomeKeyNotification, NSWindow.didResignKeyNotification, NSWindow.willCloseNotification] {
                observations.append(NotificationCenter.default.addObserver(forName:name,object:nil,queue:.main) { [weak self, weak view] note in
                    guard let self, let view else { return }
                    if let window=note.object as? NSWindow, window !== view.window { return }
                    MainActor.assumeIsolated { self.runtime.diagnostics.record("native.lifecycle", ["notification":note.name.rawValue,"active":NSApp.isActive,"windowVisible":view.window?.isVisible ?? false])
                    self.snapshot(view, "native.snapshot") }
                })
            }
        }
        func snapshot(_ view: WKWebView, _ event: String) {
            view.evaluateJavaScript("""
            ({hidden:document.hidden,focus:document.hasFocus(),ready:document.readyState,
              cards:document.querySelectorAll('.resource-card').length,
              animations:document.getAnimations().length,
              running:document.getAnimations().filter(a=>a.playState==='running').length,
              heroOpacity:getComputedStyle(document.querySelector('#hero-title')).opacity,
              heroFilter:getComputedStyle(document.querySelector('#hero-title')).filter})
            """) { [weak self] value,_ in
                if let row=value as? [String:Any] { self?.runtime.diagnostics.record(event,row) }
            }
        }
        deinit { for item in observations { NotificationCenter.default.removeObserver(item) } }
        func webView(_ view: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) { runtime.diagnostics.record("webview.navigation-start") }
        func webView(_ view: WKWebView, didCommit navigation: WKNavigation!) { runtime.diagnostics.record("webview.commit") }
        func webView(_ view: WKWebView, didFinish navigation: WKNavigation!) { runtime.pageError=nil; runtime.diagnostics.record("webview.finish"); snapshot(view,"webview.snapshot") }
        func userContentController(_ controller:WKUserContentController,didReceive message:WKScriptMessage) {
            guard message.frameInfo.isMainFrame, let url=message.frameInfo.request.url,
                  url.host=="127.0.0.1",url.port==runtime.port else { return }
            if message.name=="libraryDiagnostics", let row=message.body as? [String:Any] {
                let allowed=["event","ms","renderMs","cards","total","hidden","frames","p50","p95","max","over33","animations","running","ghosts","mode","phase","heroOpacity","heroFilter"]
                runtime.diagnostics.record("qa." + (row["event"] as? String ?? "unknown"),row.filter { allowed.contains($0.key) })
            }
            if message.name=="libraryState",let busy=message.body as? Bool {runtime.controlsBlocked=busy}
            if message.name=="libraryMotion",let mode=message.body as? String,["studio","calm"].contains(mode){runtime.motionCalm=mode=="calm"}
        }
        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy)->Void) {
            guard let url=action.request.url else { decisionHandler(.cancel);return }
            let blobOrigin = url.scheme == "blob" ? URL(string:String(url.absoluteString.dropFirst(5))) : nil
            if (url.host=="127.0.0.1" && url.port==runtime.port) || (blobOrigin?.host=="127.0.0.1" && blobOrigin?.port==runtime.port) {
                decisionHandler(action.shouldPerformDownload ? .download : .allow)
            } else {
                if ["https","http"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }
                decisionHandler(.cancel)
            }
        }
        func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy)->Void) {
            decisionHandler(response.canShowMIMEType ? .allow : .download)
        }
        func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate=self }
        func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { download.delegate=self }
        func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?)->Void) {
            let panel=NSSavePanel();panel.nameFieldStringValue=suggestedFilename
            panel.begin { result in completionHandler(result == .OK ? panel.url : nil) }
        }
        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for action: WKNavigationAction, windowFeatures: WKWindowFeatures)->WKWebView? {
            if let url=action.request.url, ["http","https"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }; return nil
        }
        func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?)->Void) {
            let panel=NSOpenPanel();panel.allowsMultipleSelection=parameters.allowsMultipleSelection;panel.canChooseDirectories=parameters.allowsDirectories;panel.canChooseFiles=true
            panel.begin { response in completionHandler(response == .OK ? panel.urls : nil) }
        }
        func webView(_ view: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            guard (error as NSError).code != NSURLErrorCancelled else { return }
            runtime.diagnostics.record("webview.navigation-failure",["code":(error as NSError).code]); runtime.pageError="管理页面载入中断。请重试。"
        }
        func webViewWebContentProcessDidTerminate(_ view: WKWebView) {
            runtime.diagnostics.record("webview.content-terminated"); runtime.pageError="页面进程已停止。收藏保存在本机，请重新打开页面。"
        }
        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { guard (error as NSError).code != NSURLErrorCancelled else { return }; runtime.diagnostics.record("webview.provisional-failure",["code":(error as NSError).code]); runtime.pageError="管理页面无法载入。请重试。" }
    }
}

struct FunctionalGlass<Content:View>: View {
    @ViewBuilder var content: Content
    var body: some View {
        if #available(macOS 26.0, *) { GlassEffectContainer(spacing:12) { content }.glassEffect(.regular.interactive(), in:.capsule) }
        else { content.background(.regularMaterial,in:Capsule()) }
    }
}
struct CaptureDock: View {
    var calm:Bool
    var collect: () -> Void
    var importFiles: () -> Void
    var pair: () -> Void
    @State private var expanded = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Namespace private var glassNamespace
    private func toggle() { withAnimation(reduceMotion || calm ? nil : .spring(response:0.38,dampingFraction:0.82)) { expanded.toggle() } }
    private func finish(_ action: () -> Void) { expanded = false; action() }
    @ViewBuilder private var controls: some View {
        if #available(macOS 26.0, *) {
            GlassEffectContainer(spacing:16) {
                HStack(spacing:12) {
                    if expanded {
                        Button { finish(collect) } label: { Label("收藏网址",systemImage:"link").padding(.horizontal,18).padding(.vertical,14) }
                            .buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("collect",in:glassNamespace)
                        Button { finish(importFiles) } label: { Label("添加素材",systemImage:"square.and.arrow.down").padding(.horizontal,18).padding(.vertical,14) }
                            .buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("files",in:glassNamespace)
                        Button { toggle() } label: { Image(systemName:"xmark").frame(width:46,height:46) }
                            .buttonStyle(.plain).glassEffect(.regular.interactive(),in:.circle).glassEffectID("close",in:glassNamespace).accessibilityLabel("收起收藏入口")
                    } else {
                        Button { toggle() } label: { Label("收藏",systemImage:"plus").padding(.horizontal,22).padding(.vertical,14) }
                            .buttonStyle(.plain).glassEffect(.regular.interactive(),in:.capsule).glassEffectID("collect",in:glassNamespace).accessibilityLabel("展开收藏入口")
                    }
                    Button(action:pair) { Image(systemName:"puzzlepiece.extension").frame(width:46,height:46) }
                        .buttonStyle(.plain).glassEffect(.regular.interactive(),in:.circle).glassEffectID("pair",in:glassNamespace).accessibilityLabel("浏览器扩展")
                }
            }
        } else {
            HStack(spacing:12) {
                if expanded {
                    Button("收藏网址",systemImage:"link") { finish(collect) }
                    Button("添加素材",systemImage:"square.and.arrow.down") { finish(importFiles) }
                }
                Button(expanded ? "收起" : "收藏",systemImage:expanded ? "xmark" : "plus") { toggle() }
                Button("浏览器扩展",systemImage:"puzzlepiece.extension",action:pair)
            }.padding(12).background(.regularMaterial,in:Capsule()).foregroundStyle(.primary)
        }
    }
    var body: some View { controls.fixedSize().font(.system(size:14,weight:.semibold)).foregroundStyle(Color(red:215/255,green:1,blue:101/255)) }
}
struct LibraryWindow: View {
    @ObservedObject var runtime: LibraryRuntime
    @State var search = ""
    @State var pairingOpen = false
    @State var phoneSyncOpen = false
    @State var copied = false
    @FocusState var searchFocused: Bool
    var body: some View {
        ZStack {
            Color(red:12/255,green:13/255,blue:16/255).ignoresSafeArea()
            if runtime.ready {
                ManagementView(runtime:runtime).frame(maxWidth:.infinity,maxHeight:.infinity)
                if let problem=runtime.pageError { VStack(spacing:16){Text(problem); Button("重新打开页面"){runtime.retryPage()}}.padding(28).background(.regularMaterial,in:RoundedRectangle(cornerRadius:20)) }
            }
            else if let error=runtime.error {
                VStack(spacing:20) { Image(systemName:"exclamationmark.triangle").font(.largeTitle);Text("资源库暂时无法打开").font(.title2);Text(error).foregroundStyle(.secondary).multilineTextAlignment(.center)
                    HStack { Button("重新启动"){runtime.start()};Button("打开日志"){NSWorkspace.shared.open(runtime.dataDirectory.appendingPathComponent("desktop.log"))} }
                }.padding(40).frame(maxWidth:520)
            } else { VStack(spacing:12){ProgressView();Text("正在打开你的资源库…").foregroundStyle(.secondary)} }
        }
        .overlay(alignment:.bottomTrailing) {
            if runtime.ready && runtime.pageError == nil && !runtime.controlsBlocked {
                CaptureDock(calm:runtime.motionCalm,collect:{runtime.command("add")},importFiles:{runtime.command("import-files")},pair:{copied=false;pairingOpen=true})
                    .padding(.trailing,30).padding(.bottom,26)
            }
        }
        .frame(minWidth:760,minHeight:550)
        .preferredColorScheme(.dark)
        .toolbar {
            ToolbarItem(placement:.automatic){Button("手机同步",systemImage:"iphone"){phoneSyncOpen=true}.disabled(!runtime.ready)}
            ToolbarItem(placement:.principal) {
                HStack(spacing:9) { Image(systemName:"magnifyingglass").foregroundStyle(.secondary);TextField("搜索资源、素材与灵感",text:$search).textFieldStyle(.plain).frame(width:250).focused($searchFocused).onChange(of:search){_,value in runtime.command("search",value:value)} }
                .padding(.horizontal,12).padding(.vertical,8)
            }
        }
        .sheet(isPresented:$phoneSyncOpen){PhoneSyncPanel(baseURL:runtime.base)}
        .sheet(isPresented:$pairingOpen) {
            VStack(alignment:.leading,spacing:20) {
                HStack { Text("把浏览器和拾集连接起来").font(.title2.weight(.semibold));Spacer();Button { pairingOpen=false } label:{Image(systemName:"xmark")}.buttonStyle(.plain).accessibilityLabel("关闭配对") }
                Text("浏览网页时保存链接、选中文字、图片或截图，回到 App 就能看到。无需账号，内容留在本机。").foregroundStyle(.secondary)
                VStack(alignment:.leading,spacing:10) {
                    Text("1. 安装浏览器扩展").font(.headline)
                    Text("Chrome 或 Edge 打开扩展管理，开启开发者模式，再加载解压的扩展文件夹。").foregroundStyle(.secondary)
                    Button("显示扩展文件夹",systemImage:"folder"){runtime.revealExtension()}
                }
                Divider()
                VStack(alignment:.leading,spacing:10) {
                    Text("2. 配对到这个 App").font(.headline)
                    Text("打开扩展的配对设置，填写下面地址，并粘贴配对码。").foregroundStyle(.secondary)
                    Text(runtime.base.absoluteString).font(.system(.body,design:.monospaced)).textSelection(.enabled)
                    FunctionalGlass { Button(copied ? "已复制配对码" : "复制配对码",systemImage:"doc.on.doc"){runtime.copyPairing();copied=true}.buttonStyle(.plain).padding(.horizontal,20).padding(.vertical,12).disabled(runtime.pairing.isEmpty || runtime.pairingLoading) }
                    if runtime.pairingLoading { ProgressView("正在读取配对码…") }
                    if let error = runtime.pairingError { HStack { Text(error).foregroundStyle(.secondary); Button("重试") { Task { await runtime.readPairing() } } } }
                    Text("配对码仅保存在本机，请勿发给其他人。").font(.caption).foregroundStyle(.secondary)
                }
                Text("窗口关闭后采集服务仍运行；退出拾集后暂停采集。收藏记录会保留。").font(.caption).foregroundStyle(.secondary)
            }.padding(30).frame(width:520).task{await runtime.readPairing()}
        }
        .onReceive(NotificationCenter.default.publisher(for:Notification.Name("ShijiSearch"))){_ in searchFocused=true}
        .onReceive(NotificationCenter.default.publisher(for:NSApplication.willTerminateNotification)){_ in runtime.stop()}
        .onOpenURL { url in if url.scheme=="shiji",url.host=="library" { runtime.command("refresh");NSApp.activate(ignoringOtherApps:true) } }
        .task { NSApp.setActivationPolicy(.regular); NSApp.activate(ignoringOtherApps:true); runtime.start() }
    }
}
@MainActor final class LibraryAppDelegate: NSObject, NSApplicationDelegate {
    weak var runtime: LibraryRuntime?
    func applicationWillTerminate(_ notification:Notification){runtime?.stop()}
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows:Bool)->Bool {
        runtime?.diagnostics.record("window.reopen",["visible":hasVisibleWindows])
        if !hasVisibleWindows { sender.windows.first(where:{$0.identifier?.rawValue=="library"})?.makeKeyAndOrderFront(nil) };return true
    }
}
@main struct ResourceLibraryApp: App {
    @NSApplicationDelegateAdaptor(LibraryAppDelegate.self) var delegate
    @StateObject var runtime=LibraryRuntime()
    var body: some Scene {
        WindowGroup("拾集 · 开发资源库",id:"library") { LibraryWindow(runtime:runtime).task{delegate.runtime=runtime} }
            .defaultSize(width:1180,height:820)
            .windowStyle(.automatic)
            .handlesExternalEvents(matching:["library"])
            .commands { CommandGroup(after:.textEditing){Button("搜索资源"){NotificationCenter.default.post(name:Notification.Name("ShijiSearch"),object:nil)}.keyboardShortcut("k")}
                CommandGroup(replacing:.newItem){Button("收藏资源"){runtime.command("add")}.keyboardShortcut("n")} }
    }
}
