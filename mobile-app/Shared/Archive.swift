import Foundation
import CryptoKit
struct LibraryError: LocalizedError { var message:String; var errorDescription:String? { message } }
func fail(_ message:String)->LibraryError { LibraryError(message:message) }
struct PortableZIP {
    static let maxFile=64*1024*1024, maxTotal=512*1024*1024
    static func read(_ data:Data) throws -> [String:Data] {
        guard data.count<=maxTotal,data.count>=22 else { throw fail("备份过大或不是有效 ZIP。手机端最多导入 512 MB。") }
        func number(_ p:Int,_ n:Int) throws -> Int { guard p>=0,p+n<=data.count else { throw fail("ZIP 文件不完整。") };return (0..<n).reduce(0){$0 | Int(data[p+$1])<<($1*8)} }
        var end:Int?
        for p in stride(from:data.count-22,through:max(0,data.count-65557),by:-1) { if try number(p,4)==0x06054b50, p+22+(try number(p+20,2))==data.count { end=p;break } }
        guard let end,try number(end+4,2)==0,try number(end+6,2)==0 else { throw fail("不支持分卷或超大 ZIP。") }
        let count=try number(end+10,2),start=try number(end+16,4),length=try number(end+12,4)
        guard count<=20000,start+length<=end else { throw fail("ZIP 目录不正确。") }
        var cursor=start,total=0,result=[String:Data]()
        for _ in 0..<count {
            guard try number(cursor,4)==0x02014b50 else { throw fail("ZIP 目录损坏。") }
            let flags=try number(cursor+8,2),method=try number(cursor+10,2),crc=try number(cursor+16,4),compressed=try number(cursor+20,4),size=try number(cursor+24,4),names=try number(cursor+28,2),extra=try number(cursor+30,2),comment=try number(cursor+32,2),offset=try number(cursor+42,4),attrs=try number(cursor+38,4)
            guard flags&1==0,[0,8].contains(method),size<=maxFile,compressed<=maxTotal,cursor+46+names+extra+comment<=start+length else { throw fail("备份包含加密、不支持的压缩或超过 64 MB 的单个文件。") }
            guard let name=String(data:data.subdata(in:cursor+46..<cursor+46+names),encoding:.utf8),!name.hasPrefix("/"),!name.contains("\\"),!name.split(separator:"/").contains(".."),!name.contains("\0"),attrs>>16 & 0xf000 != 0xa000,result[name]==nil else { throw fail("备份包含不安全或重复路径。") }
            total+=size;guard total<=maxTotal,try number(offset,4)==0x04034b50 else { throw fail("备份解压后超过 512 MB 或文件损坏。") }
            let localNameLength=try number(offset+26,2)
            guard offset+30+localNameLength<=data.count,try number(offset+8,2)==method,try number(offset+6,2)==flags,String(data:data.subdata(in:offset+30..<offset+30+localNameLength),encoding:.utf8)==name else {throw fail("ZIP 本地目录与中央目录不一致。")}
            let from=try offset+30+localNameLength+number(offset+28,2)
            guard from+compressed<=start else { throw fail("备份文件边界无效。") }
            let packed=data.subdata(in:from..<from+compressed)
            var bytes:Data
            if method==0 { guard packed.count==size else { throw fail("ZIP 大小校验失败。") };bytes=packed }
            else { bytes=Data(count:max(size,1));let good=bytes.withUnsafeMutableBytes { out in packed.withUnsafeBytes { input in shiji_inflate(input.bindMemory(to:UInt8.self).baseAddress,input.count,out.bindMemory(to:UInt8.self).baseAddress,size) } };guard good==1 else { throw fail("ZIP 解压失败。") };bytes.count=size }
            let actual=bytes.withUnsafeBytes{shiji_crc($0.bindMemory(to:UInt8.self).baseAddress,$0.count)}
            guard Int(actual)==crc else { throw fail("ZIP 校验失败，文件可能损坏。") }
            result[name]=bytes;cursor+=46+names+extra+comment
        }
        guard cursor==start+length else { throw fail("ZIP 目录长度无效。") };return result
    }
    static func write(_ entries:[String:Data]) throws -> Data {
        var archive=Data(),central=Data()
        func put(_ value:Int,_ n:Int,_ output:inout Data) { for i in 0..<n { output.append(UInt8(truncatingIfNeeded:value>>(8*i))) } }
        guard entries.count<=20000,entries.values.reduce(0,{$0+$1.count})<=maxTotal else { throw fail("手机端完整备份上限为 512 MB。") }
        for name in entries.keys.sorted() {
            let bytes=entries[name]!,encoded=Data(name.utf8),offset=archive.count
            guard bytes.count<=maxFile else { throw fail("附件超过手机端单文件 64 MB 上限。") }
            let crc=bytes.withUnsafeBytes{Int(shiji_crc($0.bindMemory(to:UInt8.self).baseAddress,$0.count))}
            put(0x04034b50,4,&archive);for v in [20,0x800,0,0,0] { put(v,2,&archive) };for v in [crc,bytes.count,bytes.count] {put(v,4,&archive)};put(encoded.count,2,&archive);put(0,2,&archive);archive.append(encoded);archive.append(bytes)
            put(0x02014b50,4,&central);for v in [20,20,0x800,0,0,0] {put(v,2,&central)};for v in [crc,bytes.count,bytes.count] {put(v,4,&central)};for v in [encoded.count,0,0,0,0] {put(v,2,&central)};put(0,4,&central);put(offset,4,&central);central.append(encoded)
        }
        let start=archive.count;archive.append(central);put(0x06054b50,4,&archive);for v in [0,0,entries.count,entries.count] {put(v,2,&archive)};put(central.count,4,&archive);put(start,4,&archive);put(0,2,&archive);return archive
    }
}
