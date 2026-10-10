# iPhone Share Extension专项计划（未标记修复）

本轮未更改 iPhone 主 App 或扩展。已有 QA 模拟器空白页仍是未解决问题；原生存储、ZIP 和实际 HTTPS 客户端测试通过，不证明系统分享表单和真机链路通过。

源码审查依据：`mobile-app/ShareExtension/ShareViewController.swift`、扩展 Info.plist、两个 target 的 entitlements、`Shared/Library.swift`、Xcode 工程及 `mobile-app/README.md`。入口为 `$(PRODUCT_MODULE_NAME).ShareViewController`，App Group 来自两个 target 的 `SHIJI_APP_GROUP`。当前控制器先显示 loading 表单，再读取 providers；共享容器访问发生在保存时。因此仅凭 App Group 配置不能解释初始表单空白，必须区分“扩展未启动”“hosting 未绘制”和“保存失败”。这是源码推断，尚无本轮系统分享运行证据。

1. 建立独立 QA Bundle ID、App Group、模拟器及临时收藏，不复用正式 Keychain/配对。记录 OS/SDK、宿主来源和扩展实例。检查安装后的扩展包、实际展开的 principal class、签名 entitlements、provisioning 与运行时共享容器路径；源码字符串相同不足以证明权限有效。真机签名与 Group 能力需用户的有效 Apple Team 配置。
2. 从 Safari URL、纯文本来源和照片分别启动真实系统分享。利用已有 OSLog 的 viewDidLoad/viewDidAppear/layout/provider 日志定位：控制器是否启动、root/host bounds 是否非零、host 是否进入 window、loading 是否可见。在隔离实验中用可见 UIKit 基准视图定位宿主/布局，再对照 SwiftUI hosting；确定原因后才更改实现。
3. 验证 URL、文本、UIImage/Data/文件 URL 的真实 NSItemProvider 回调；失败、空 provider、取消、重复打开、超限图片、不支持类型必须显示可恢复状态。日志只记录类型、阶段、大小和错误码，不记录分享内容。不要用任意延迟或反复 reload 掩盖空白。
4. 真实保存 → 扩展结束 → 主 App 出现：核对 stable ID、完整逗号标签、原名称/备注保留、附件原字节及封面；关闭/取消不写入。模拟器测试与真机测试分别记录，保留 Safari/照片宿主截图和连续录屏。
5. 冷/热启动、系统深浅色、Reduce Motion、Dynamic Type、窄宽度、离线和文件暂不可读均验收。最后才验证同一 Wi-Fi 与隔离电脑双向同步、冲突和附件，并确认没有覆盖已有手工编辑。

完成标准：真实 Share Extension 表单可见、失败可恢复、三类来源保存可回读、取消无变化、共享目录和签名在运行环境得到验证；编译或核心测试成功不能替代以上结果。
