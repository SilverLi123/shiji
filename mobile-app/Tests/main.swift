import Foundation
func check(_ value: Bool,_ label:String){if !value{fatalError(label)}}
let temp=FileManager.default.temporaryDirectory.appendingPathComponent("shiji-ios-tests-"+UUID().uuidString,isDirectory:true)
defer{try? FileManager.default.removeItem(at:temp)}
let library=try LibraryFiles(root:temp)
let id=try library.capture(url:"https://example.com/ref",title:"Reference",text:"first",attachment:(Data([0x89,0x50,0x4e,0x47,13,10,26,10]),"test.png","image/png"))
var record=try library.resources()[0].raw;record["tags"]=["New, exact"];record["title"]="Edited";record["projectNotes"]=["__proto__":"kept"]
try library.save(record)
let queue=DispatchQueue(label:"capture",attributes:.concurrent),group=DispatchGroup()
for i in 0..<16 {group.enter();queue.async{defer{group.leave()};do{try LibraryFiles(root:temp).capture(url:"https://example.com/ref",title:"Old",text:"capture-\(i)-end")}catch{fatalError("capture failed: \(error)")}}};group.wait()
let saved=try library.resources()[0];check(saved.title=="Edited","title preserved");check(saved.names("tags")==["New, exact"],"comma tag preserved")
for i in 0..<16 {check(saved.text("notes").contains("capture-\(i)-end"),"concurrent selection retained")}
let archive=try library.exportZIP(),plan=try library.preview(archive);check(plan.resources.count==1&&plan.fileCount==1,"archive round trip")
let restored=try LibraryFiles(root:temp.appendingPathComponent("restored"));check(try restored.merge(plan)==1,"import adds");check(try restored.merge(plan)==0,"duplicate import skips")
try library.set(id,key:"deleted",value:true);check(try library.resources()[0].flag("deleted"),"trash");try library.set(id,key:"deleted",value:false);check(try library.resources()[0].flag("deleted")==false,"restore")
var broken=archive;broken[35]^=1;do{_ = try PortableZIP.read(broken);fatalError("corrupt zip accepted")}catch{}
let evil=try PortableZIP.write(["../escape":Data("bad".utf8)]);do{_ = try PortableZIP.read(evil);fatalError("unsafe path accepted")}catch{}
let json=try JSONSerialization.data(withJSONObject:["version":1,"schemaVersion":3,"resources":[saved.raw],"collections":["Project"]]);let metadata=try library.preview(json);check(metadata.fileCount==0&&metadata.resources[0].attachments.isEmpty&&metadata.resources[0].text("coverId").isEmpty,"JSON attachment warning contract")
if CommandLine.arguments.count>1 {let directory=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true);try archive.write(to:directory.appendingPathComponent("mobile-roundtrip.zip"))}
let base=try library.resources()[0].raw
try library.capture(url:"https://example.com/ref",title:"Ignored",text:"concurrent new note")
var stale=base;stale["title"]="Stale edit"
do{try library.save(stale,expected:base);fatalError("stale editor overwrote capture")}catch{}
check(try library.resources()[0].text("notes").contains("concurrent new note"),"stale editor retains capture")
if CommandLine.arguments.count>2 {let desktop=try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]));let input=try library.preview(desktop);check(input.resources.count==1&&input.fileCount==3,"real desktop deflate/ZIP64-local import");check(try restored.merge(input)==1,"desktop import");check(try restored.resources().contains{$0.title=="From desktop"},"desktop title")}
print("Shared persistence, 16 concurrent captures, comma tags, trash, JSON/ZIP roundtrip, corrupt/path ZIP tests passed")
// Preflight and cancel are read-only, and collision rollback protects old bytes.
let beforePreview=try Data(contentsOf:library.database)
_ = try library.preview(archive)
check(try Data(contentsOf:library.database)==beforePreview,"preflight cancellation leaves database unchanged")
var entries=try PortableZIP.read(archive)
let attachmentPath=entries.keys.first{$0.hasPrefix("files/")}!
entries[attachmentPath]!.append(0)
let corruptAttachment=try PortableZIP.write(entries)
do{_ = try library.preview(corruptAttachment);fatalError("checksum/size mismatch accepted")}catch{}
var sameCoverPlan=plan
var independent=sameCoverPlan.resources[0].raw
independent["id"]="independent";independent["url"]="https://example.com/independent"
sameCoverPlan.resources=[Resource(raw:independent)]
let oldDatabase=try Data(contentsOf:restored.database)
let oldCover=try Data(contentsOf:restored.files.appendingPathComponent(saved.text("coverId")))
do{_ = try restored.merge(sameCoverPlan);fatalError("attachment collision accepted")}catch{}
check(try Data(contentsOf:restored.database)==oldDatabase,"collision leaves database unchanged")
check(try Data(contentsOf:restored.files.appendingPathComponent(saved.text("coverId")))==oldCover,"collision preserves attachment bytes")
try library.set(id,key:"deleted",value:true)
let trashZIP=try library.exportZIP()
check(try library.preview(trashZIP).resources[0].flag("deleted"),"trash state survives ZIP")
if CommandLine.arguments.count>1{try trashZIP.write(to:URL(fileURLWithPath:CommandLine.arguments[1]).appendingPathComponent("mobile-trash.zip"))}
print("Preflight cancellation, checksum rejection, collision atomicity and trash backup passed")

var invalid=LibraryFiles.newRecord(title:"Missing website URL")
do{try library.save(invalid);fatalError("empty website accepted")}catch{}
invalid["url"]="https://example.com/long";invalid["title"]=String(repeating:"x",count:201)
do{try library.save(invalid);fatalError("nonportable long title accepted")}catch{}
check(try LibraryFiles.normalize("https://EXAMPLE.COM:443")=="https://example.com/","desktop URL normalization")
print("Desktop PDF/text fixtures, website URL, title limits and URL normalization passed")
// Three-way sync protects independent edits instead of timestamp-based overwrites.
let syncBase=Resource(raw:LibraryFiles.newRecord(title:"Base",url:"https://example.com/sync"))
var localEdit=syncBase;localEdit.raw["notes"]="Phone note";localEdit.raw["tags"]=["New, exact"]
var remoteEdit=syncBase;remoteEdit.raw["notes"]="Computer note"
let firstPush=try SyncMerge.plan(phone:[localEdit],computer:[],base:[])
check(firstPush.uploads.count==1&&firstPush.conflicts.isEmpty,"first phone push")
let firstPull=try SyncMerge.plan(phone:[],computer:[remoteEdit],base:[])
check(firstPull.resources.count==1&&firstPull.uploads.isEmpty,"first computer pull")
check(try SyncMerge.plan(phone:[localEdit],computer:[syncBase],base:[syncBase]).uploads.count==1,"phone edit push")
check(try SyncMerge.plan(phone:[syncBase],computer:[remoteEdit],base:[syncBase]).resources[0].text("notes")=="Computer note","desktop edit pull")
let conflict=try SyncMerge.plan(phone:[localEdit],computer:[remoteEdit],base:[syncBase]);check(conflict.conflicts.count==1,"concurrent edits require choice")
let chosen=try SyncMerge.plan(phone:[localEdit],computer:[remoteEdit],base:[syncBase],choices:[syncBase.id:"phone"]);check(chosen.conflicts.isEmpty&&chosen.resources[0].names("tags")==["New, exact"],"explicit choice exact tags")
var duplicate=localEdit;duplicate.raw["id"]=UUID().uuidString.lowercased()
let dedup=try SyncMerge.plan(phone:[duplicate],computer:[remoteEdit],base:[]);check(dedup.conflicts.count==1&&dedup.conflicts[0].id==remoteEdit.id,"same URL uses desktop identity with conflict")
var trashed=syncBase;trashed.raw["deleted"]=true
check(try SyncMerge.plan(phone:[trashed],computer:[syncBase],base:[syncBase]).uploads[0].flag("deleted"),"trash travels")
check(try SyncMerge.plan(phone:[syncBase],computer:[],base:[syncBase]).conflicts.count==1,"missing formerly synced record is not silently purged")
let syncStore=try LibraryFiles(root:temp.appendingPathComponent("sync"));try syncStore.save(syncBase.raw)
let expectedSync=try syncStore.resources()
let snap=try SyncSnapshot(["version":1,"libraryId":UUID().uuidString,"revision":String(repeating:"a",count:64),"resources":[remoteEdit.raw]])
try syncStore.applySync(snap,expected:expectedSync,payloads:[:]);check(try syncStore.resources()[0].text("notes")=="Computer note","guarded apply")
try syncStore.capture(url:syncBase.text("url"),title:"Ignored",text:"Late share")
do{try syncStore.applySync(snap,expected:expectedSync,payloads:[:]);fatalError("sync overwrote late share")}catch{}
check(try syncStore.resources()[0].text("notes").contains("Late share"),"late share survives")
print("Sync first merge, both directions, duplicate identity, conflicts, trash and late-share protection passed")

var sameURLCopy=syncBase.raw;sameURLCopy["id"]=UUID().uuidString.lowercased()
let identicalDuplicate=Resource(raw:sameURLCopy)
check(try SyncMerge.plan(phone:[identicalDuplicate],computer:[syncBase],base:[]).conflicts.count==1,"distinct identical URL records require explicit identity choice")
check(try SyncMerge.plan(phone:[syncBase],computer:[identicalDuplicate],base:[syncBase]).conflicts.count==1,"purged and recreated record requires explicit identity choice")
let replaced=try SyncMerge.plan(phone:[syncBase],computer:[identicalDuplicate],base:[syncBase],choices:[identicalDuplicate.id:"computer"])
check(replaced.conflicts.isEmpty&&replaced.resources.count==1&&replaced.resources[0].id==identicalDuplicate.id,"explicit recreated identity resolves once")
print("Identical URL identity collisions and recreated records require visible choices")

var formerB=LibraryFiles.newRecord(title:"Former B",url:"https://example.com/former-b")
var movedB=formerB;movedB["url"]=syncBase.text("url")
let collidedBase=try SyncMerge.plan(phone:[syncBase],computer:[Resource(raw:movedB)],base:[syncBase,Resource(raw:formerB)])
check(collidedBase.conflicts.count==1,"base identity collision returns conflict without duplicate-key trap")

do{_ = try SyncMerge.plan(phone:[syncBase,Resource(raw:formerB)],computer:[Resource(raw:movedB)],base:[syncBase,Resource(raw:formerB)]);fatalError("ambiguous URL reuse accepted")}catch{check(error.localizedDescription.contains("电脑另一条记录"),"ambiguous URL reuse offers accurate reconciliation guidance")}

check(Resource(raw:["kind":"code"]).presentation=="text","code presentation")
check(Resource(raw:["kind":"prompt"]).presentation=="text","prompt presentation")
check(Resource(raw:["kind":"website","category":"开发工具"]).presentation=="tool","tool presentation")
check(Resource(raw:["kind":"file"]).presentation=="visual","visual presentation")
check(Resource(raw:["kind":"code"]).raw["presentation"]==nil,"presentation is not persisted")
print("V2 resource presentation derivation leaves schema untouched")
check(LibraryFiles.quickTitle("https://github.com/openai/codex")=="openai/codex · GitHub","quick repository title")
check(LibraryFiles.quickTitle("https://example.com/page")=="example.com","offline quick hostname")
let quick=try LibraryFiles(root:temp.appendingPathComponent("quick"))
let quickRaw=LibraryFiles.newRecord(title:LibraryFiles.quickTitle("https://example.com/offline"),url:"https://example.com/offline",kind:"website")
try quick.save(quickRaw)
check(try LibraryFiles(root:quick.root).resources()[0].title=="example.com","quick capture is durable without network")
print("V2 offline quick capture persists hostname and repository titles")

let coverRecord=Resource(raw:["kind":"website","url":"https://github.com/SilverLi123/shiji","title":"SHIJI","language":"Swift"])
check(coverRecord.coverKind=="tool" && coverRecord.repositoryPath=="SilverLi123/shiji","real repository cover")
check(Resource(raw:["kind":"website","url":"https://github.com.evil.test/repo"]).coverKind=="editorial","exact cover hostname")
let codeCover=Resource(raw:["kind":"code","snippet":"  let x = 1\n\n  print(x)","notes":"other"])
check(codeCover.coverLines==["  let x = 1","","  print(x)"],"code whitespace and empty lines retained")
check(Resource(raw:["kind":"prompt","description":"real description","notes":"note"]).coverContent=="real description","real cover fallback")
check(codeCover.raw["coverKind"]==nil && codeCover.raw["coverLines"]==nil,"native cover fields never serialized")
check(Resource(raw:["kind":"code","snippet":String(repeating:"line\n",count:1000)]).coverLines.count==7,"bounded native preview")
print("V2.1 native real-field covers, exact host, whitespace, bounded previews and schema preservation passed")
