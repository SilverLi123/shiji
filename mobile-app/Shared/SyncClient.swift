import Foundation
import Security
import CryptoKit

struct SyncConnection:Codable {
    var address:String,port:Int,certificate:Data,authority:Data,secret:String,token:String,libraryID:String,computerName:String,deviceID:String
    static func parse(_ code:String,allowLoopback:Bool=false) throws -> SyncConnection {
        guard code.utf8.count<=12000,let url=URLComponents(string:code.trimmingCharacters(in:.whitespacesAndNewlines)),url.scheme=="shiji-sync",url.host=="pair",let items=url.queryItems,items.count==6,Set(items.map(\.name))==Set(["v","address","port","certificate","authority","secret"]) else{throw fail("配对码不完整，请从电脑重新复制。")}
        var q=[String:String]();for item in items{guard q[item.name]==nil,let value=item.value else{throw fail("配对码字段重复。")};q[item.name]=value}
        guard q["v"]=="1",let address=q["address"],privateAddress(address,allowLoopback:allowLoopback),let port=Int(q["port"] ?? ""),(1...65535).contains(port),let certificate=Data(base64Encoded:q["certificate"] ?? ""),let authority=Data(base64Encoded:q["authority"] ?? ""),certificate.count<=4096,authority.count<=4096,SecCertificateCreateWithData(nil,certificate as CFData) != nil,SecCertificateCreateWithData(nil,authority as CFData) != nil,let secret=q["secret"],secret.count>=32,secret.count<=80 else{throw fail("配对地址或证书无效。请在电脑选择同一 Wi-Fi 的地址后生成新码。")}
        return SyncConnection(address:address,port:port,certificate:certificate,authority:authority,secret:secret,token:"",libraryID:"",computerName:"",deviceID:UUID().uuidString.lowercased())
    }
    static func privateAddress(_ value:String,allowLoopback:Bool)->Bool {
        let parts=value.split(separator:".");guard parts.count==4,parts.allSatisfy({!$0.isEmpty && $0.allSatisfy(\.isNumber) && $0.count<=3}),let a=Int(parts[0]),let b=Int(parts[1]),parts.allSatisfy({Int($0).map{(0...255).contains($0)} ?? false})else{return false}
        return a==10 || a==192 && b==168 || a==172 && (16...31).contains(b) || allowLoopback && a==127
    }
    var base:URL{URL(string:"https://\(address):\(port)")!}
}
enum SyncCredentials {
    private static var query:[String:Any]{[kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"local.silver.shiji.computer-sync",kSecAttrAccount as String:"paired-computer"]}
    static func load() throws -> SyncConnection? {var q=query;q[kSecReturnData as String]=true;q[kSecMatchLimit as String]=kSecMatchLimitOne;var result:CFTypeRef?;let status=SecItemCopyMatching(q as CFDictionary,&result);if status==errSecItemNotFound{return nil};guard status==errSecSuccess,let bytes=result as? Data else{throw fail("暂时无法读取配对信息，请解锁 iPhone 后重试。")};return try JSONDecoder().decode(SyncConnection.self,from:bytes)}
    static func save(_ value:SyncConnection) throws {let bytes=try JSONEncoder().encode(value);let update=[kSecValueData as String:bytes];var status=SecItemUpdate(query as CFDictionary,update as CFDictionary);if status==errSecItemNotFound{var q=query;q[kSecValueData as String]=bytes;q[kSecAttrAccessible as String]=kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly;status=SecItemAdd(q as CFDictionary,nil)};guard status==errSecSuccess else{throw fail("无法保存电脑配对，请解锁手机后重试。")}}
    static func forget() throws {let status=SecItemDelete(query as CFDictionary);guard status==errSecSuccess || status==errSecItemNotFound else{throw fail("无法解除配对，请稍后重试。")}}
}
final class SyncHTTP:NSObject,URLSessionDataDelegate,URLSessionTaskDelegate,@unchecked Sendable {
    private let connection:SyncConnection,lock=NSLock()
    private struct Response {var data=Data();var response:HTTPURLResponse?;let limit:Int;let continuation:CheckedContinuation<Data,Error>;var failure:Error?}
    private var requests=[Int:Response]()
    private var trustFailure:Error?
    private lazy var session:URLSession={let config=URLSessionConfiguration.ephemeral;config.timeoutIntervalForRequest=20;config.timeoutIntervalForResource=120;return URLSession(configuration:config,delegate:self,delegateQueue:nil)}()
    init(_ connection:SyncConnection){self.connection=connection}
    func close(){session.invalidateAndCancel()}
    func request(_ path:String,method:String="GET",body:Data?=nil,limit:Int=64*1024*1024,headers:[String:String]=[:]) async throws -> Data {
        var request=URLRequest(url:connection.base.appendingPathComponent(path));request.httpMethod=method;request.httpBody=body
        if !connection.token.isEmpty{request.setValue("Bearer "+connection.token,forHTTPHeaderField:"Authorization")}
        if body != nil{request.setValue("application/json",forHTTPHeaderField:"Content-Type")}
        for(k,v)in headers{request.setValue(v,forHTTPHeaderField:k)}
        return try await withCheckedThrowingContinuation{continuation in let task=session.dataTask(with:request);lock.lock();requests[task.taskIdentifier]=Response(limit:limit,continuation:continuation);lock.unlock();task.resume()}
    }
    func json(_ path:String,method:String="GET",value:[String:Any]?=nil) async throws -> [String:Any] {let body=try value.map{try JSONSerialization.data(withJSONObject:$0)};guard (body?.count ?? 0)<=64*1024*1024 else{throw fail("同步信息超过上限。")};let bytes=try await request(path,method:method,body:body);guard let value=try JSONSerialization.jsonObject(with:bytes) as? [String:Any]else{throw fail("电脑响应格式不正确。")};return value}
    func urlSession(_ session:URLSession,dataTask:URLSessionDataTask,didReceive response:URLResponse,completionHandler:@escaping(URLSession.ResponseDisposition)->Void){lock.lock();defer{lock.unlock()};guard var record=requests[dataTask.taskIdentifier],let response=response as? HTTPURLResponse else{completionHandler(.cancel);return};record.response=response;if response.expectedContentLength>Int64(record.limit){record.failure=fail("电脑响应超过上限。");requests[dataTask.taskIdentifier]=record;completionHandler(.cancel)}else{requests[dataTask.taskIdentifier]=record;completionHandler(.allow)}}
    func urlSession(_ session:URLSession,dataTask:URLSessionDataTask,didReceive data:Data){lock.lock();defer{lock.unlock()};guard var record=requests[dataTask.taskIdentifier]else{return};if record.data.count+data.count>record.limit{record.failure=fail("同步响应超过上限。");requests[dataTask.taskIdentifier]=record;dataTask.cancel()}else{record.data.append(data);requests[dataTask.taskIdentifier]=record}}
    func urlSession(_ session:URLSession,task:URLSessionTask,didCompleteWithError error:Error?){lock.lock();let result=requests.removeValue(forKey:task.taskIdentifier);let trustError=trustFailure;lock.unlock();guard let result else{return};if let failure=result.failure ?? trustError ?? error{result.continuation.resume(throwing:failure);return};guard let response=result.response,(200...299).contains(response.statusCode)else{let problem=(try? JSONSerialization.jsonObject(with:result.data) as? [String:Any])?["error"] as? String ?? "电脑同步失败，请重试。";result.continuation.resume(throwing:NSError(domain:"ShijiSyncHTTP",code:result.response?.statusCode ?? 0,userInfo:[NSLocalizedDescriptionKey:problem]));return};result.continuation.resume(returning:result.data)}
    func urlSession(_ session:URLSession,task:URLSessionTask,willPerformHTTPRedirection response:HTTPURLResponse,newRequest request:URLRequest,completionHandler:@escaping(URLRequest?)->Void){completionHandler(nil)}
    func urlSession(_ session:URLSession,didReceive challenge:URLAuthenticationChallenge,completionHandler:@escaping(URLSession.AuthChallengeDisposition,URLCredential?)->Void){
        func reject(_ reason:String){lock.lock();trustFailure=fail("电脑证书验证失败："+reason);lock.unlock();completionHandler(.cancelAuthenticationChallenge,nil)}
        guard challenge.protectionSpace.authenticationMethod==NSURLAuthenticationMethodServerTrust else{reject("验证方式不符");return}
        guard challenge.protectionSpace.host==connection.address else{reject("地址不符");return}
        guard let trust=challenge.protectionSpace.serverTrust else{reject("缺少证书链");return}
        guard let chain=SecTrustCopyCertificateChain(trust) as? [SecCertificate],let leaf=chain.first else{reject("缺少服务器证书");return}
        guard SecCertificateCopyData(leaf) as Data==connection.certificate else{reject("服务器证书与配对记录不符，请重新配对");return}
        guard let anchor=SecCertificateCreateWithData(nil,connection.authority as CFData)else{reject("配对证书无效");return}
        var evaluated:SecTrust?
        guard SecTrustCreateWithCertificates([leaf,anchor] as CFArray,SecPolicyCreateSSL(true,connection.address as CFString),&evaluated)==errSecSuccess,let evaluated else{reject("无法构建证书链");return}
        SecTrustSetAnchorCertificates(evaluated,[anchor] as CFArray);SecTrustSetAnchorCertificatesOnly(evaluated,true);SecTrustSetNetworkFetchAllowed(evaluated,false)
        var trustError:CFError?
        guard SecTrustEvaluateWithError(evaluated,&trustError)else{reject(trustError.map{CFErrorCopyDescription($0) as String} ?? "证书已失效");return};completionHandler(.useCredential,URLCredential(trust:evaluated))
    }
}
struct PreparedSync {let local:[Resource],remote:SyncSnapshot,base:[Resource],plan:SyncPlan}
enum SyncExchange {
    static func pair(_ connection:SyncConnection,name:String) async throws -> SyncConnection {let http=SyncHTTP(connection);defer{http.close()};let result=try await http.json("sync/pair",method:"POST",value:["secret":connection.secret,"deviceId":connection.deviceID,"name":name]);guard let token=result["token"] as? String,token.count>=32,let library=result["libraryId"] as? String,UUID(uuidString:library) != nil else{throw fail("电脑配对响应无效。")};var paired=connection;paired.token=token;paired.secret="";paired.libraryID=library;paired.computerName=result["computerName"] as? String ?? "我的电脑";return paired}
    static func prepare(_ connection:SyncConnection,files:LibraryFiles,base:[Resource]) async throws -> PreparedSync {let http=SyncHTTP(connection);defer{http.close()};let remote=try SyncSnapshot(await http.json("sync/snapshot"));guard remote.libraryID==connection.libraryID else{throw fail("电脑当前打开了不同资源库。请解除配对后重新连接。")};let local=try files.resources();let plan=try SyncMerge.plan(phone:local,computer:remote.resources,base:base);return PreparedSync(local:local,remote:remote,base:base,plan:plan)}
    static func commit(_ prepared:PreparedSync,connection:SyncConnection,files:LibraryFiles,choices:[String:String]=[:]) async throws -> SyncSnapshot {
        guard try SyncMerge.fullSnapshot(files.resources())==SyncMerge.fullSnapshot(prepared.local)else{throw fail("手机收藏刚刚变化，请重新同步。")}
        let plan=try SyncMerge.plan(phone:prepared.local,computer:prepared.remote.resources,base:prepared.base,choices:choices)
        guard plan.conflicts.isEmpty else{throw fail("请先选择冲突资源的版本。")}
        let http=SyncHTTP(connection);defer{http.close()};var transferred=0
        let known=Dictionary(uniqueKeysWithValues:prepared.remote.resources.flatMap(\.attachments).compactMap{a in (a["id"] as? String).map{($0,a)}})
        for r in plan.uploads{for a in r.attachments{let id=a["id"] as! String;if let old=known[id]{guard old["sha256"] as? String==a["sha256"] as? String else{throw fail("两端同 ID 附件内容不同，未覆盖文件。")};continue};guard let path=files.file(id)else{throw fail("手机附件缺失，请从有效备份恢复。")};let bytes=try Data(contentsOf:path);transferred+=bytes.count;guard transferred<=PortableZIP.maxTotal,bytes.count==a["size"] as? Int,SHA256.hash(data:bytes).map({String(format:"%02x",$0)}).joined()==a["sha256"] as? String else{throw fail("手机附件校验失败或本次传输超过 512 MB。")};_ = try await http.request("sync/files/"+id,method:"PUT",body:bytes,headers:["Content-Type":"application/octet-stream","X-Shiji-SHA256":a["sha256"] as! String])}}
        let result:SyncSnapshot
        if plan.uploads.isEmpty{result=prepared.remote}else{result=try SyncSnapshot(await http.json("sync/commit",method:"POST",value:["version":1,"libraryId":connection.libraryID,"expectedRevision":prepared.remote.revision,"requestId":UUID().uuidString.lowercased(),"resources":plan.uploads.map(\.raw)]))}
        var payloads=[String:Data]()
        for r in result.resources{for a in r.attachments{let id=a["id"] as! String;if files.file(id)==nil{let bytes=try await http.request("sync/files/"+id,limit:PortableZIP.maxFile);transferred+=bytes.count;guard transferred<=PortableZIP.maxTotal else{throw fail("本次同步超过 512 MB，请分批导入素材。")};payloads[id]=bytes}}}
        try files.applySync(result,expected:prepared.local,payloads:payloads);return result
    }
}
