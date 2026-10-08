import Foundation

@main struct Integration {
    static func check(_ condition:Bool,_ label:String){if !condition{fatalError(label)}}
    static func main() async throws {
        let root=URL(fileURLWithPath:CommandLine.arguments[1]),mode=CommandLine.arguments[2]
        let files=try LibraryFiles(root:root.appendingPathComponent("phone"))
        let credential=root.appendingPathComponent("test-connection.json"),checkpoint=root.appendingPathComponent("checkpoint.json")
        let connection:SyncConnection
        if mode=="first" {
            let parsed=try SyncConnection.parse(String(contentsOf:root.appendingPathComponent("pairing-code.txt"),encoding:.utf8),allowLoopback:true)
            connection=try await SyncExchange.pair(parsed,name:"Temporary QA phone")
            try JSONEncoder().encode(connection).write(to:credential)
            let id=try files.capture(url:"https://example.com/phone-sync",title:"Phone resource",text:"Phone original",attachment:(Data(contentsOf:root.appendingPathComponent("fixture.jpg")),"cover.jpg","image/jpeg"))
            var r=try files.resources().first{$0.id==id}!.raw;r["tags"]=["New, exact"];try files.save(r)
        }else{connection=try JSONDecoder().decode(SyncConnection.self,from:Data(contentsOf:credential))}
        let base=FileManager.default.fileExists(atPath:checkpoint.path) ? try SyncSnapshot(JSONSerialization.jsonObject(with:Data(contentsOf:checkpoint)) as! [String:Any]).resources : []
        if mode=="second" || mode=="conflict"{let r=try files.resources().first{$0.text("url")=="https://example.com/phone-sync"}!;try files.set(r.id,key:"notes",value:mode=="second" ? "Phone second edit" : "Phone conflict edit")}
        if mode=="pin" {var bad=connection;bad.certificate=bad.authority;do{_ = try await SyncExchange.prepare(bad,files:files,base:base);fatalError("wrong certificate pin accepted")}catch{};print("PASS: incorrect certificate pin rejected");return}
        let prepared=try await SyncExchange.prepare(connection,files:files,base:base)
        if mode=="race"{try files.capture(url:"https://example.com/late",title:"Late capture",text:"");do{_ = try await SyncExchange.commit(prepared,connection:connection,files:files);fatalError("late capture overwritten")}catch{};check(try files.resources().contains{$0.title=="Late capture"},"late record survived");print("PASS: late local capture rejects stale sync");return}
        let result:SyncSnapshot
        if mode=="conflict"{check(prepared.plan.conflicts.count==1,"concurrent edit conflict not found");do{_ = try await SyncExchange.commit(prepared,connection:connection,files:files);fatalError("unresolved conflict committed")}catch{};let id=prepared.plan.conflicts[0].id;result=try await SyncExchange.commit(prepared,connection:connection,files:files,choices:[id:"computer"])}
        else{check(prepared.plan.conflicts.isEmpty,"unexpected conflict");result=try await SyncExchange.commit(prepared,connection:connection,files:files)}
        try JSONSerialization.data(withJSONObject:result.metadata).write(to:checkpoint)
        let all=try files.resources();check(all.count==2,"resources missing");let phone=all.first{$0.text("url")=="https://example.com/phone-sync"}!
        check(phone.names("tags")==["New, exact"],"comma tag split")
        let image=phone.attachments[0];check(try Data(contentsOf:files.file(image["id"] as! String)!)==Data(contentsOf:root.appendingPathComponent("fixture.jpg")),"attachment bytes changed")
        if mode=="second"{check(all.first{$0.text("url")=="https://example.com/computer-sync"}!.text("notes")=="Computer second edit","desktop edit missing")}
        if mode=="conflict"{check(phone.text("notes")=="Computer conflict edit","chosen computer version not applied")}
        print("PASS: real HTTPS Swift–desktop \(mode) sync, exact tags and verified attachments")
    }
}
