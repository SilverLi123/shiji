import Foundation
import CryptoKit

struct SyncSnapshot {
    let libraryID:String,revision:String,resources:[Resource]
    let metadata:[String:Any]
    init(_ raw:[String:Any]) throws {
        guard raw["version"] as? Int==1,let id=raw["libraryId"] as? String,UUID(uuidString:id) != nil,let revision=raw["revision"] as? String,revision.range(of:"^[a-f0-9]{64}$",options:.regularExpression) != nil,let records=raw["resources"] as? [[String:Any]],records.count<=10000 else{throw fail("电脑同步数据无效，请更新两端 App。")}
        self.libraryID=id;self.revision=revision;self.resources=records.map{Resource(raw:$0)};self.metadata=raw
        try Self.validate(resources)
    }
    static func validate(_ records:[Resource]) throws {
        var ids=Set<String>(),urls=Set<String>(),attachments=Set<String>()
        for r in records {
            try LibraryFiles.validateMetadata(r.raw)
            guard LibraryFiles.idOK(r.id),ids.insert(r.id).inserted else{throw fail("同步资源 ID 无效或重复。")}
            let url=try LibraryFiles.normalize(r.text("url"));guard url.isEmpty || urls.insert(url).inserted else{throw fail("同步数据含重复网址。")}
            for a in r.attachments{guard let id=a["id"] as? String,UUID(uuidString:id) != nil,attachments.insert(id).inserted,a["resourceId"] as? String==r.id,let hash=a["sha256"] as? String,hash.range(of:"^[a-f0-9]{64}$",options:.regularExpression) != nil,let size=a["size"] as? Int,size>0,size<=PortableZIP.maxFile,let name=a["name"] as? String,!name.isEmpty,name.unicodeScalars.count<=240 else{throw fail("同步附件格式不正确。")}}
            guard r.text("coverId").isEmpty || r.attachments.contains(where:{$0["id"] as? String==r.text("coverId") && ($0["mime"] as? String ?? "").hasPrefix("image/")})else{throw fail("同步封面引用无效。")}
        }
    }
}
struct SyncConflict:Identifiable {
    let id:String,phone:Resource?,computer:Resource?
    var identityCollision=false
    var title:String{phone?.title ?? computer?.title ?? "已移除的资源"}
}
struct SyncPlan {
    let resources:[Resource],uploads:[Resource],conflicts:[SyncConflict]
}
enum SyncMerge {
    static func canonical(_ value:Any) throws -> Data {try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys,.withoutEscapingSlashes])}
    static func same(_ a:Resource?,_ b:Resource?) throws -> Bool {
        guard let a,let b else{return a==nil && b==nil}
        func semantic(_ resource:Resource)->[String:Any]{var r=resource.raw;for k in ["id","createdAt","updatedAt","linkStatus","linkCheckedAt","linkMessage"]{r.removeValue(forKey:k)};if r["coverConfig"] is NSNull{r.removeValue(forKey:"coverConfig")};r["deleted"]=resource.flag("deleted");r["attachments"]=resource.attachments.sorted{($0["id"] as? String ?? "")<($1["id"] as? String ?? "")};return r}
        return try canonical(semantic(a))==canonical(semantic(b))
    }
    static func fullSnapshot(_ records:[Resource]) throws -> Data {try canonical(records.sorted{$0.id<$1.id}.map(\.raw))}
    static func plan(phone:[Resource],computer:[Resource],base:[Resource],choices:[String:String]=[:]) throws -> SyncPlan {
        try SyncSnapshot.validate(phone);try SyncSnapshot.validate(computer);try SyncSnapshot.validate(base)
        let remote=Dictionary(uniqueKeysWithValues:computer.map{($0.id,$0)})
        var byURL=[String:String]();for r in computer where !r.text("url").isEmpty{byURL[try LibraryFiles.normalize(r.text("url"))]=r.id}
        var aliases=[String:String]();let phoneIDs=Set(phone.map(\.id))
        for r in phone where remote[r.id]==nil && !r.text("url").isEmpty{if let id=byURL[try LibraryFiles.normalize(r.text("url"))]{guard !phoneIDs.contains(id)else{throw fail("电脑另一条记录使用了手机已有的网址。请先在电脑恢复原记录或调整该网址，再同步；两端收藏均已保留。")};aliases[r.id]=id}}
        func remap(_ r:Resource)->Resource {var raw=r.raw;let rid=aliases[r.id] ?? r.id;raw["id"]=rid;raw["attachments"]=r.attachments.map{a in var a=a;a["resourceId"]=rid;return a};if let parent=aliases[r.text("parentId")]{raw["parentId"]=parent};return Resource(raw:raw)}
        var local=[String:Resource]();for r in phone{let mapped=remap(r);guard local[mapped.id]==nil else{throw fail("手机含同网址的重复记录，请先整理后同步。")};local[mapped.id]=mapped}
        let previous=Dictionary(uniqueKeysWithValues:base.map{($0.id,$0)})
        var merged=[Resource](),uploads=[Resource](),conflicts=[SyncConflict]()
        for id in Set(local.keys).union(remote.keys).union(previous.keys).sorted(){
            let l=local[id],r=remote[id],b=previous[id];var chosen:Resource?
            if Set(aliases.values).contains(id),l != nil,r != nil{conflicts.append(SyncConflict(id:id,phone:l,computer:r,identityCollision:true))}
            else if try same(l,r){chosen=r ?? l}
            else if b==nil {if l==nil{chosen=r}else if r==nil{chosen=l}else{conflicts.append(SyncConflict(id:id,phone:l,computer:r))}}
            else if l==nil || r==nil {conflicts.append(SyncConflict(id:id,phone:l,computer:r))}
            else if try same(l,b){chosen=r}
            else if try same(r,b){chosen=l}
            else{conflicts.append(SyncConflict(id:id,phone:l,computer:r))}
            if let choice=choices[id],conflicts.last?.id==id {
                guard ["phone","computer"].contains(choice)else{throw fail("请选择手机或电脑版本。")}
                chosen=choice=="phone" ? l : r
                if chosen==nil,let surviving=l ?? r{var raw=surviving.raw;raw["deleted"]=true;chosen=Resource(raw:raw)}
                conflicts.removeLast()
            }
            if let chosen{merged.append(chosen);if try !same(chosen,r){uploads.append(chosen)}}
        }
        if conflicts.isEmpty{try SyncSnapshot.validate(merged)}
        return SyncPlan(resources:merged,uploads:uploads,conflicts:conflicts)
    }
}
