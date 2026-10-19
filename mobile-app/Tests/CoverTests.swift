import Foundation
@main struct CoverTests {
 static func check(_ value:Bool,_ label:String){if !value{fatalError(label)}}
 static func json(_ value:Any?) throws -> Data {try JSONSerialization.data(withJSONObject:[value ?? NSNull()],options:[.sortedKeys,.withoutEscapingSlashes])}
 static func main() throws {
  let vectors=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [String:Any]
  for c in vectors["valid"] as! [[String:Any]] {
   let normalized=try CoverConfiguration.normalize(c["input"])
   if let want=c["want"]{check(try json(normalized)==json(want),"shared config vector \(c["name"]!)")}
   if let subset=c["subset"] as? [String:Any]{for (key,want) in subset{check(try json(normalized?[key])==json(want),"shared subset \(key)")}}
  }
  for value in vectors["invalid"] as! [Any]{do{_ = try CoverConfiguration.normalize(value);fatalError("invalid config accepted \(value)")}catch{}}
  for value:[String:Any] in [["customTitle":String(repeating:"中",count:201)],["customSubtitle":String(repeating:"s",count:241)],["extra":String(repeating:"中",count:3000)],["imageX":Double.nan],["extra":Double.infinity]]{do{_ = try CoverConfiguration.normalize(value);fatalError("unbounded config accepted")}catch{}}
  check(try CoverConfiguration.normalize(nil)==nil,"absent auto")
  for c in vectors["directions"] as! [[String:Any]]{let direction=CoverConfiguration.direction(Resource(raw:c["resource"] as! [String:Any]));check(direction.style==c["style"] as? String && direction.template==c["template"] as? String,"native/desktop content direction mismatch")}
  check(CoverConfiguration.colors(["primary":"#777777"]).foreground=="#000000","mid-gray contrast must use true black")
  for source in ["auto","image","website","poster"]{check(CoverConfiguration.usesDraftImage(["imageSource":source]) == ["auto","image"].contains(source),"pending upload must obey selected source")}
  let captionedCode=Resource(raw:["kind":"code","snippet":"let answer = 42","coverConfig":["style":"developer","template":"a","customSubtitle":"CUSTOM SUBTITLE QA"]])
  check(CoverConfiguration.subtitle(captionedCode,automatic:false)=="CUSTOM SUBTITLE QA","explicit code subtitle remains visible when automatic excerpt is suppressed")
  let longCode=Resource(raw:["snippet":"a"+String(repeating:"\u{0301}",count:10000)])
  check(longCode.coverLines.first!.unicodeScalars.count<=160,"preview bounds must count scalars, not giant grapheme clusters")
  check(longCode.coverExcerpt.unicodeScalars.count<=240,"poster excerpts must not shape full 100K content")
  let root=FileManager.default.temporaryDirectory.appendingPathComponent("shiji-cover-tests-"+UUID().uuidString);defer{try? FileManager.default.removeItem(at:root)}
  let files=try LibraryFiles(root:root);let record=LibraryFiles.newRecord(title:"Original title",kind:"file");try files.save(record);let id=record["id"] as! String
  let base=try files.resources()[0]
  let first=try files.updateCover(id,config:["style":"spatial","customTitle":"Cover only","extension":["keep":true]],coverID:"",expectedConfig:nil,expectedCoverID:"")
  check(first.title=="Original title","cover never renames source");check((first.raw["coverConfig"] as? [String:Any])?["customTitle"] as? String=="Cover only","preference persisted")
  check(try LibraryFiles(root:root).resources()[0].raw["coverConfig"] != nil,"restart preserves config")
  let before=try Data(contentsOf:files.database)
  try FileManager.default.setAttributes([.modificationDate:Date(timeIntervalSince1970:10)],ofItemAtPath:files.database.path)
  _ = try files.updateCover(id,config:["style":"spatial","customTitle":"Cover only","extension":["keep":true]],coverID:"",expectedConfig:nil,expectedCoverID:"")
  check(try Data(contentsOf:files.database)==before,"identical retry unchanged")
  check(try files.database.resourceValues(forKeys:[.contentModificationDateKey]).contentModificationDate==Date(timeIntervalSince1970:10),"identical retry performs no write")
  try files.save(["id":id,"title":"Edited source","kind":"file","notes":"Keep notes"])
  let edited=try files.updateCover(id,config:["style":"editorial"],coverID:"",expectedConfig:first.raw["coverConfig"],expectedCoverID:"")
  check(edited.title=="Edited source" && edited.text("notes")=="Keep notes","field guard merges unrelated edits")
  do{_ = try files.updateCover(id,config:["style":"minimal"],coverID:"",expectedConfig:first.raw["coverConfig"],expectedCoverID:"");fatalError("stale cover overwritten")}catch{}
  let png=Data(base64Encoded:"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNQXvTiPwAFRgKtws1megAAAABJRU5ErkJggg==")!
  let image=try files.updateCover(id,config:["style":"minimal","imageSource":"image"],coverID:"",expectedConfig:edited.raw["coverConfig"],expectedCoverID:"",upload:(png,"actual.png","image/png"))
  check(image.attachments.count==1 && !image.text("coverId").isEmpty,"native upload publishes one selected attachment")
  let retry=try files.updateCover(id,config:["style":"minimal","imageSource":"image"],coverID:"",expectedConfig:edited.raw["coverConfig"],expectedCoverID:"",upload:(png,"renamed.png","image/png"))
  check(retry.attachments.count==1 && retry.text("coverId")==image.text("coverId"),"renamed/retried bytes deduplicated")
  do{_ = try files.updateCover(id,config:nil,coverID:image.text("coverId"),expectedConfig:image.raw["coverConfig"],expectedCoverID:image.text("coverId"),upload:(Data("broken".utf8),"bad.png","image/png"));fatalError("broken image accepted")}catch{}
  let reset=try files.updateCover(id,config:nil,coverID:image.text("coverId"),expectedConfig:image.raw["coverConfig"],expectedCoverID:image.text("coverId"))
  check(reset.raw["coverConfig"] is NSNull && reset.attachments.count==1,"explicit null reset retains image bytes")
  var omitted=reset.raw;omitted.removeValue(forKey:"coverConfig")
  check(try SyncMerge.same(reset,Resource(raw:omitted)),"null and missing auto do not create sync conflict")
  var future=reset.raw;future["coverConfig"]=["version":9,"style":"future","opaque":["preserved":true]];try files.save(future)
  do{_ = try files.updateCover(id,config:["style":"editorial"],coverID:image.text("coverId"),expectedConfig:future["coverConfig"],expectedCoverID:image.text("coverId"));fatalError("future config flattened")}catch{}
  let auto=try files.updateCover(id,config:nil,coverID:image.text("coverId"),expectedConfig:future["coverConfig"],expectedCoverID:image.text("coverId"))
  var phone=auto.raw,computer=auto.raw;phone["coverConfig"]=["style":"developer"];computer["coverConfig"]=["style":"kinetic"]
  check(try SyncMerge.plan(phone:[Resource(raw:phone)],computer:[Resource(raw:computer)],base:[auto]).conflicts.count==1,"both-end art changes stay visible conflicts")
  let customized=try files.updateCover(id,config:["style":"developer","template":"b","customTitle":"跨端封面","imageSource":"image","imageX":12,"extension":["keep":true]],coverID:image.text("coverId"),expectedConfig:nil,expectedCoverID:image.text("coverId"))
  let output=URL(fileURLWithPath:CommandLine.arguments[2],isDirectory:true);try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true);try files.exportZIP().write(to:output.appendingPathComponent("mobile-cover.zip"))
  if CommandLine.arguments.count>3{let archive=try files.preview(Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[3])));let desktop=archive.resources.first{$0.title=="From desktop"}!;check((desktop.raw["coverConfig"] as? [String:Any])?["customTitle"] as? String=="Desktop cover","desktop ZIP preferences reach phone");check(archive.files[desktop.text("coverId")] != nil,"desktop ZIP real selected image reaches phone")}
  check(base.raw["coverConfig"]==nil && customized.title=="Edited source","original old record remains independent")
  print("PASS: shared native cover values, guarded atomic preferences/upload/retry, legacy/future/null, sync conflicts and real ZIP exchange")
 }
}
