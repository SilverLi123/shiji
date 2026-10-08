import Foundation
import CryptoKit
struct Resource: Identifiable {
    var raw:[String:Any]
    var id:String { raw["id"] as? String ?? "" }
    func text(_ key:String)->String {raw[key] as? String ?? ""}
    func flag(_ key:String)->Bool {raw[key] as? Bool ?? false}
    func names(_ key:String)->[String] {raw[key] as? [String] ?? []}
    var title:String {text("title")}
    // Presentation is derived, never serialized into schema 3.
    var presentation:String {
        if ["code","prompt"].contains(text("kind")){return "text"}
        return text("kind")=="website" && text("category")=="开发工具" ? "tool" : "visual"
    }
    var attachments:[[String:Any]] {raw["attachments"] as? [[String:Any]] ?? []}
}
struct ImportPlan { var manifest:[String:Any];var files:[String:Data];var resources:[Resource];var fileCount:Int {files.count} }
final class LibraryFiles: @unchecked Sendable {
    let root:URL
    private let lock=NSLock()
    var database:URL {root.appendingPathComponent("library.json")}
    var files:URL {root.appendingPathComponent("files",isDirectory:true)}
    init(root:URL) throws {self.root=root;try FileManager.default.createDirectory(at:files,withIntermediateDirectories:true)}
    static func appRoot() throws -> URL {
        let group=Bundle.main.object(forInfoDictionaryKey:"ShijiAppGroup") as? String ?? "group.local.silver.shiji"
        #if os(iOS)
        guard let root=FileManager.default.containerURL(forSecurityApplicationGroupIdentifier:group) else {throw fail("共享收藏目录不可用。请在 Xcode 为 App 和分享扩展配置同一个 App Group 后重新安装。")};return root.appendingPathComponent("Library",isDirectory:true)
        #else
        throw fail("测试必须明确指定临时目录。")
        #endif
    }
    private func empty()->[String:Any] {["version":1,"schemaVersion":3,"resources":[[String:Any]](),"collections":[String](),"collectionMeta":[[String:Any]](),"smartCollections":[[String:Any]]()]}
    private func access<T>(write:Bool,_ operation:(inout [String:Any]) throws -> T) throws -> T {
        lock.lock();defer{lock.unlock()};var coordinatorError:NSError?,result:Result<T,Error>?
        let body:(URL)->Void={ url in result=Result { var value=self.empty();if FileManager.default.fileExists(atPath:url.path){guard let parsed=try JSONSerialization.jsonObject(with:Data(contentsOf:url)) as? [String:Any],parsed["schemaVersion"] as? Int==3 else {throw fail("本机收藏文件损坏，未覆盖原文件。")};value=parsed};let output=try operation(&value);if write {let bytes=try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]);
            #if os(iOS)
            try bytes.write(to:url,options:[.atomic,.completeFileProtectionUntilFirstUserAuthentication])
            #else
            try bytes.write(to:url,options:.atomic)
            #endif
        };return output } }
        let coordinator=NSFileCoordinator()
        if write {coordinator.coordinate(writingItemAt:database,options:.forMerging,error:&coordinatorError,byAccessor:body)} else {coordinator.coordinate(readingItemAt:database,options:[],error:&coordinatorError,byAccessor:body)}
        if let coordinatorError {throw coordinatorError};guard let result else{throw fail("收藏文件暂时无法读取，请重试。")};return try result.get()
    }
    func resources() throws -> [Resource] {try access(write:false){($0["resources"] as? [[String:Any]] ?? []).map{Resource(raw:$0)}}}
    func applySync(_ snapshot:SyncSnapshot,expected:[Resource],payloads:[String:Data]) throws {
        try SyncSnapshot.validate(snapshot.resources)
        let required=Set(snapshot.resources.flatMap(\.attachments).compactMap{$0["id"] as? String})
        guard Set(payloads.keys).isSubset(of:required),payloads.values.reduce(0,{$0+$1.count})<=PortableZIP.maxTotal else{throw fail("同步附件列表无效或超过上限。")}
        var written=[URL]()
        do {try access(write:true){data in
            let current=(data["resources"] as? [[String:Any]] ?? []).map{Resource(raw:$0)}
            guard try SyncMerge.fullSnapshot(current)==SyncMerge.fullSnapshot(expected)else{throw fail("手机收藏刚刚变化，未覆盖新内容。请重新同步。")}
            for r in snapshot.resources{for a in r.attachments{
                let aid=a["id"] as! String,target=self.files.appendingPathComponent(aid)
                let bytes:Data
                if FileManager.default.fileExists(atPath:target.path){guard !(try target.resourceValues(forKeys:[.isSymbolicLinkKey]).isSymbolicLink ?? false)else{throw fail("同步附件路径无效。")};bytes=try Data(contentsOf:target)}else{guard let value=payloads[aid]else{throw fail("同步附件尚未下载完成。")};bytes=value}
                guard bytes.count==a["size"] as? Int,Self.detectedMIME(bytes)==a["mime"] as? String,SHA256.hash(data:bytes).map({String(format:"%02x",$0)}).joined()==a["sha256"] as? String else{throw fail("同步附件校验失败，原文件保留。")}
            }}
            for (aid,bytes) in payloads{let target=self.files.appendingPathComponent(aid);if !FileManager.default.fileExists(atPath:target.path){try bytes.write(to:target,options:.atomic);written.append(target)}}
            data["resources"]=snapshot.resources.map(\.raw)
            data["collectionMeta"]=snapshot.metadata["collectionMeta"] ?? []
            data["smartCollections"]=snapshot.metadata["smartCollections"] ?? []
            data["collections"]=Array(Set((snapshot.metadata["collections"] as? [String] ?? [])+snapshot.resources.flatMap{$0.names("projects")})).sorted()
        }}catch{for path in written{try? FileManager.default.removeItem(at:path)};throw error}
    }
    static func normalize(_ value:String) throws -> String {
        let value=value.trimmingCharacters(in:.whitespacesAndNewlines)
        guard !value.isEmpty else{return ""};guard var c=URLComponents(string:value),["http","https"].contains(c.scheme?.lowercased() ?? ""),let host=c.host,!host.isEmpty,c.user==nil,c.password==nil,value.count<=4000,!value.contains(where:{$0.isWhitespace}) else {throw fail("请输入有效的 HTTP 或 HTTPS 网址。")};c.scheme=c.scheme?.lowercased();c.host=host.lowercased();c.fragment=nil;if c.port==(c.scheme=="https" ? 443 : 80){c.port=nil};if c.path.isEmpty{c.path="/"};return c.string ?? value
    }
    static func idOK(_ value:String)->Bool {!value.isEmpty&&value.count<=80&&value.range(of:"^[A-Za-z0-9_-]+$",options:.regularExpression) != nil}
    static func timestamp()->String {ISO8601DateFormatter().string(from:Date())}
    static func newRecord(title:String,url:String="",kind:String="website")->[String:Any] {
        ["id":UUID().uuidString.lowercased(),"title":title,"url":url,"kind":kind,"category":"其他","description":"","notes":"","tags":[String](),"projects":[String](),"projectNotes":[String:String](),"collection":"","colors":[String](),"price":"待确认","license":"待确认","licenseUrl":"","sourceUrl":url,"author":"","parentId":"","coverId":"","thumbnail":"","favicon":"","favorite":false,"inbox":true,"demo":false,"deleted":false,"createdAt":timestamp(),"updatedAt":timestamp(),"linkStatus":"unchecked","linkCheckedAt":"","attachments":[[String:Any]]()]
    }
    static func validateMetadata(_ record:[String:Any]) throws {
        guard let title=record["title"] as? String,!title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty,title.unicodeScalars.count<=200 else{throw fail("请填写不超过 200 字的资源名称。")}
        let kind=record["kind"] as? String ?? "website"
        guard ["website","file","code","prompt"].contains(kind) else{throw fail("资源形式无效。")}
        let address=try normalize(record["url"] as? String ?? "")
        guard kind != "website" || !address.isEmpty else{throw fail("网站资源需要填写网址。")}
        for (key,limit) in [("description",1000),("notes",10000),("author",200),("snippet",100000),("language",40)]{if let value=record[key]{guard let text=value as? String,text.unicodeScalars.count<=limit else{throw fail("字段格式不正确或太长。")}}}
        for key in ["sourceUrl","licenseUrl","thumbnail","favicon"]{if let value=record[key]{guard let text=value as? String else{throw fail("来源网址格式不正确。")};_ = try normalize(text)}}
        for (key,choices) in [("category",["开发工具","美术素材","UI / 设计","音频","视频","字体","3D","灵感","其他"]),("price",["待确认","免费","部分免费","付费"]),("license",["待确认","允许商用","需署名","仅个人使用"])]{if let value=record[key]{guard let text=value as? String,choices.contains(text)else{throw fail("资源分类或授权无效。")}}}
        for key in ["tags","projects"]{if let value=record[key]{guard let names=value as? [String],names.count<=30,names.allSatisfy({!$0.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty && $0.unicodeScalars.count<=(key=="tags" ? 50 : 80)}) else{throw fail("标签或项目名称无效、过长或超过 30 个。")}}}
        if let value=record["projectNotes"]{guard let notes=value as? [String:String],notes.count<=1000,notes.allSatisfy({!$0.key.isEmpty && $0.key.unicodeScalars.count<=80 && $0.value.unicodeScalars.count<=2000})else{throw fail("项目备注格式无效或太长。")}}
    }
    func save(_ record:[String:Any],expected:[String:Any]?=nil) throws {
        guard let id=record["id"] as? String,Self.idOK(id),let title=record["title"] as? String,!title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty,title.unicodeScalars.count<=200 else {throw fail("请填写不超过 200 字的资源名称。")}
        try Self.validateMetadata(record)
        var clean=record;clean["url"]=try Self.normalize(record["url"] as? String ?? "");clean["updatedAt"]=Self.timestamp()
        for key in ["sourceUrl","licenseUrl"] {clean[key]=try Self.normalize(record[key] as? String ?? "")}
        for (key,limit) in [("description",1000),("notes",10000),("author",200)] {guard (record[key] as? String ?? "").count<=limit else{throw fail("字段过长，请缩短后保存。")}}
        for key in ["tags","projects"] {let values=record[key] as? [String] ?? [];guard values.count<=30,values.allSatisfy({!$0.isEmpty&&$0.count<=(key=="tags" ? 50 : 80)}) else{throw fail("标签或项目名称过长、数量超过 30。")}}
        let address=clean["url"] as? String ?? ""
        try access(write:true){data in var items=data["resources"] as? [[String:Any]] ?? [];if !address.isEmpty,items.contains(where:{$0["id"] as? String != id && $0["url"] as? String==address}){throw fail("这个网址已经收藏，请使用已有资源。")};if let i=items.firstIndex(where:{$0["id"] as? String==id}){if let expected,try JSONSerialization.data(withJSONObject:expected,options:.sortedKeys) != JSONSerialization.data(withJSONObject:items[i],options:.sortedKeys){throw fail("收藏已被其他入口修改。你的草稿已保留，请取消后重新打开编辑。")};var current=items[i];for (key,value) in clean{current[key]=value};items[i]=current}else{if let url=clean["url"] as? String,!url.isEmpty,items.contains(where:{$0["url"] as? String==url}){throw fail("这个网址已经收藏，请打开已有资源编辑。")};items.insert(clean,at:0)};data["resources"]=items}
    }
    @discardableResult func capture(url:String,title:String,text:String,attachment:(Data,String,String)?=nil) throws -> String {
        let url=try Self.normalize(url),title=title.trimmingCharacters(in:.whitespacesAndNewlines)
        return try access(write:true){data in var items=data["resources"] as? [[String:Any]] ?? [];let existing = !url.isEmpty ? items.firstIndex(where:{$0["url"] as? String==url}) : nil
            var record=existing.map{items[$0]} ?? Self.newRecord(title:title.isEmpty ? (URL(string:url)?.host ?? "分享的素材") : String(String.UnicodeScalarView(title.unicodeScalars.prefix(200))),url:url,kind:url.isEmpty ? (attachment==nil ? "code" : "file") : "website")
            let notes=record["notes"] as? String ?? "";if !text.isEmpty && !notes.contains(text){record["notes"]=String(String.UnicodeScalarView((notes.isEmpty ? text : notes+"\n\n"+text).unicodeScalars.prefix(10000)))};record["deleted"]=false;record["updatedAt"]=Self.timestamp()
            if let attachment {let info=try self.publish(attachment.0,name:attachment.1,mime:attachment.2,rid:record["id"] as! String);var a=record["attachments"] as? [[String:Any]] ?? [];a.append(info);record["attachments"]=a;if attachment.2.hasPrefix("image/") && (record["coverId"] as? String ?? "").isEmpty{record["coverId"]=info["id"]}}
            if let existing{items[existing]=record}else{items.insert(record,at:0)};data["resources"]=items;return record["id"] as! String
        }
    }
    static func detectedMIME(_ bytes:Data)->String {
        let b=[UInt8](bytes.prefix(16))
        if b.starts(with:[137,80,78,71,13,10,26,10]){return "image/png"}
        if b.starts(with:[255,216,255]){return "image/jpeg"}
        if String(bytes:bytes.prefix(6),encoding:.ascii).map({["GIF87a","GIF89a"].contains($0)})==true{return "image/gif"}
        if b.starts(with:[82,73,70,70]),b.count>=12 {if String(bytes:b[8..<12],encoding:.ascii)=="WEBP"{return "image/webp"};if String(bytes:b[8..<12],encoding:.ascii)=="WAVE"{return "audio/wav"}}
        if b.starts(with:[102,76,97,67]){return "audio/flac"};if b.starts(with:[79,103,103,83]){return "audio/ogg"}
        if b.starts(with:[73,68,51]) || b.count>1 && b[0]==255 && b[1]&0xe0==0xe0{return "audio/mpeg"}
        if b.count>12,String(bytes:b[4..<8],encoding:.ascii)=="ftyp"{return "video/mp4"}
        if b.starts(with:[26,69,223,163]){return "video/webm"};return "application/octet-stream"
    }
    private func publish(_ bytes:Data,name:String,mime:String,rid:String) throws -> [String:Any] {
        guard !bytes.isEmpty,bytes.count<=PortableZIP.maxFile else{throw fail("素材为空或超过手机端 64 MB 上限。")};let id=UUID().uuidString.lowercased();try bytes.write(to:files.appendingPathComponent(id),options:.atomic)
        return ["id":id,"resourceId":rid,"name":String(name.replacingOccurrences(of:"/",with:"_").prefix(240)),"size":bytes.count,"mime":Self.detectedMIME(bytes),"sha256":SHA256.hash(data:bytes).map{String(format:"%02x",$0)}.joined(),"sourceUrl":"","author":"","license":"待确认","licenseUrl":"","colors":[String](),"createdAt":Self.timestamp(),"deleted":false]
    }
    func attach(_ bytes:Data,name:String,mime:String,id:String) throws {try access(write:true){data in var records=data["resources"] as? [[String:Any]] ?? [];guard let i=records.firstIndex(where:{$0["id"] as? String==id})else{throw fail("资源已不存在。")};let a=try self.publish(bytes,name:name,mime:mime,rid:id);var all=records[i]["attachments"] as? [[String:Any]] ?? [];all.append(a);records[i]["attachments"]=all;if mime.hasPrefix("image/") && (records[i]["coverId"] as? String ?? "").isEmpty{records[i]["coverId"]=a["id"]};records[i]["updatedAt"]=Self.timestamp();data["resources"]=records}}
    func set(_ id:String,key:String,value:Any) throws {try access(write:true){data in var r=data["resources"] as? [[String:Any]] ?? [];guard let i=r.firstIndex(where:{$0["id"] as? String==id})else{throw fail("资源已不存在。")};r[i][key]=value;r[i]["updatedAt"]=Self.timestamp();data["resources"]=r}}
    func file(_ id:String) -> URL? {guard Self.idOK(id)else{return nil};let url=files.appendingPathComponent(id);return FileManager.default.fileExists(atPath:url.path) ? url : nil}
    func preview(_ bytes:Data) throws -> ImportPlan {
        let entries=bytes.starts(with:[0x50,0x4b]) ? try PortableZIP.read(bytes) : [:]
        let json=entries.isEmpty ? bytes : entries["manifest.json"] ?? Data()
        guard json.count<=64*1024*1024,let object=try JSONSerialization.jsonObject(with:json) as? [String:Any],(object["schemaVersion"] as? Int==3 || object["format"] as? String=="shiji-full-backup" && object["version"] as? Int==2),let raw=object["resources"] as? [[String:Any]],raw.count<=10000 else {throw fail("请选择拾集 schema 3 JSON 或 manifest 2 完整备份。")}
        if !entries.isEmpty {guard entries.keys.allSatisfy({$0=="manifest.json" || $0=="library.sqlite3" || $0.range(of:"^files/[a-f0-9-]{36}$",options:.regularExpression) != nil}) else{throw fail("备份包含非拾集文件。")}}
        var ids=Set<String>(),urls=Set<String>(),records=[Resource](),payloads=[String:Data]()
        for var r in raw {try Self.validateMetadata(r);guard let id=r["id"] as? String,Self.idOK(id),ids.insert(id).inserted,let title=r["title"] as? String,!title.isEmpty else {throw fail("资源名称或 ID 无效、重复。")};let url=try Self.normalize(r["url"] as? String ?? "");if !url.isEmpty {guard urls.insert(url).inserted else {throw fail("备份包含重复网址。")}};r["url"]=url;r["attachments"]=[[String:Any]]();if entries.isEmpty {r["coverId"]=""};records.append(Resource(raw:r))}
        let attachments=object["attachments"] as? [[String:Any]] ?? []
        if !entries.isEmpty {var aids=Set<String>();for a in attachments {guard let id=a["id"] as? String,id.range(of:"^[a-f0-9-]{36}$",options:.regularExpression) != nil,aids.insert(id).inserted,let rid=a["resourceId"] as? String,ids.contains(rid),let content=entries["files/"+id],let size=a["size"] as? Int,size==content.count,let hash=a["sha256"] as? String,SHA256.hash(data:content).map({String(format:"%02x",$0)}).joined()==hash else {throw fail("备份附件引用或 SHA-256 校验失败。")};guard a["mime"] as? String==Self.detectedMIME(content) else{throw fail("附件类型校验失败。")};payloads[id]=content;if let i=records.firstIndex(where:{$0.id==rid}),!(a["deleted"] as? Bool ?? false){var all=records[i].attachments;all.append(a);records[i].raw["attachments"]=all}}
            for r in records {let cover=r.text("coverId");guard cover.isEmpty || r.attachments.contains(where:{$0["id"] as? String==cover && ($0["mime"] as? String ?? "").hasPrefix("image/")})else{throw fail("备份封面引用无效。")}}
        };return ImportPlan(manifest:object,files:payloads,resources:records)
    }
    @discardableResult func merge(_ plan:ImportPlan) throws -> Int {
        var written=[URL]()
        do {return try access(write:true){data in
            var current=data["resources"] as? [[String:Any]] ?? []
            let ids=Set(current.compactMap{$0["id"] as? String}),urls=Set(current.compactMap{$0["url"] as? String}.filter{!$0.isEmpty})
            let added=plan.resources.filter{!ids.contains($0.id) && ($0.text("url").isEmpty || !urls.contains($0.text("url")))}
            let existingIDs=Set(current.flatMap{$0["attachments"] as? [[String:Any]] ?? []}.compactMap{$0["id"] as? String})
            // Validate every destination before writing any attachment; never replace an existing inode.
            for r in added {for a in r.attachments {guard let aid=a["id"] as? String,!existingIDs.contains(aid),plan.files[aid] != nil,self.file(aid)==nil else{throw fail("附件 ID 冲突，未覆盖已有收藏。")}}}
            for r in added {for a in r.attachments {let aid=a["id"] as! String,target=self.files.appendingPathComponent(aid);try plan.files[aid]!.write(to:target,options:.atomic);written.append(target)};current.append(r.raw)}
            data["resources"]=current
            for key in ["collections","collectionMeta","smartCollections"] {if (data[key] as? [Any] ?? []).isEmpty,let value=plan.manifest[key]{data[key]=value}}
            return added.count
        }} catch {for file in written{try? FileManager.default.removeItem(at:file)};throw error}
    }
    func exportZIP() throws -> Data {try access(write:false){data in var entries=[String:Data](),attachments=[[String:Any]]();let records=data["resources"] as? [[String:Any]] ?? []
        for r in records {for var a in r["attachments"] as? [[String:Any]] ?? [] {guard let id=a["id"] as? String,let url=self.file(id)else{throw fail("附件缺失，未生成不完整备份。")};let bytes=try Data(contentsOf:url);guard a["size"] as? Int==bytes.count,a["sha256"] as? String==SHA256.hash(data:bytes).map({String(format:"%02x",$0)}).joined() else {throw fail("附件已损坏，未生成备份。")};a["deleted"]=a["deleted"] as? Bool ?? false;attachments.append(a);entries["files/"+id]=bytes}}
        let manifest:[String:Any]=["format":"shiji-full-backup","version":2,"createdAt":Self.timestamp(),"resources":records,"collections":data["collections"] ?? [],"collectionMeta":data["collectionMeta"] ?? [],"smartCollections":data["smartCollections"] ?? [],"attachments":attachments];entries["manifest.json"]=try JSONSerialization.data(withJSONObject:manifest,options:[.sortedKeys]);return try PortableZIP.write(entries)
    }}
}
