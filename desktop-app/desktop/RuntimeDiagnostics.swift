import Foundation
/// Bounded metadata-only diagnostics; no resource content or pairing secrets.
final class RuntimeDiagnostics {
    let file: URL
    private let lock = NSLock()
    init(root: URL) { file = root.appendingPathComponent("runtime-events.jsonl") }
    func record(_ event: String, _ fields: [String: Any] = [:]) {
        lock.lock(); defer { lock.unlock() }
        var row = fields; row["event"] = event; row["time"] = Date().timeIntervalSince1970
        guard JSONSerialization.isValidJSONObject(row), let data = try? JSONSerialization.data(withJSONObject: row, options: [.sortedKeys]) else { return }
        do {
            try FileManager.default.createDirectory(at: file.deletingLastPathComponent(), withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            if ((try? FileManager.default.attributesOfItem(atPath:file.path)[.size] as? NSNumber)?.intValue ?? 0) > 1_048_576 {
                let old = file.appendingPathExtension("previous")
                if FileManager.default.fileExists(atPath: old.path) { try FileManager.default.removeItem(at: old) }
                try FileManager.default.moveItem(at: file, to: old)
            }
            if !FileManager.default.fileExists(atPath: file.path) { FileManager.default.createFile(atPath: file.path, contents: nil, attributes: [.posixPermissions: 0o600]) }
            let handle = try FileHandle(forWritingTo: file); defer { try? handle.close() }
            try handle.seekToEnd(); try handle.write(contentsOf: data + Data([10]))
        } catch { /* Opening the library must not depend on diagnostics. */ }
    }
}
