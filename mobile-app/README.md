# 拾集 iPhone

原生 iPhone 本地开发资源库候选源码，支持与配套 Mac 候选版在同一 Wi-Fi 双向同步，包含待修复验证的系统分享扩展。最低 iOS 17；iOS 26 起采用系统 Liquid Glass 收藏控件，旧系统使用系统材质菜单。SwiftUI / Foundation / UIKit / CryptoKit / QuickLook / Security / 系统 zlib，无第三方运行时依赖。

**当前验证限制（2026-10-11）：历史分享空白页尚未根因闭环。** 新建独立 iPhone 17 / iOS 27 QA 模拟器已实际完成系统 URL、文本、图片分享保存，以及主 App 回读；Safari 表单可见，取消后全部文件校验和不变。此前 2026-10-08 环境出现过持续空白，本次未复现；新环境通过不等同于旧故障已经修复，尚无实体 iPhone 签名安装验证。逐场景状态与真实证据见 [Next 分享专项报告](../docs/shiji-next/SHARE_REPORT.md)。此前界面微调的独立复审结论“ship reviewed refinement”只覆盖其审查范围，不是整产品批准，也不证明扫码、完整同步操作或所有辅助功能状态通过。

## 已实现

- 大图浏览；搜索资源、标签、备注；分类、常用、待整理；按项目浏览集合。
- 画廊显示当前匹配数量与附件数量；无本地封面时使用真实字段生成的工具、代码、提示词和文章排版；无障碍字号使用紧凑预览。可清除分类/范围筛选，无匹配结果时可一键清除搜索和筛选。
- 空库提供“收藏第一个资源”和“连接电脑”，隐藏重复采集浮层；辅助功能字号使用紧凑文字介绍，为两个入口保留空间。
- 原生详情、来源与授权、备注、编辑、附件预览；回车确认标签，逗号保留在名称内。
- App 内网址和本机文件收藏；编辑冲突保留草稿并提示。
- 分享扩展支持网址、文字或单张图片，并配置为与 App 使用同一 App Group；独立模拟器真实系统分享保存及主 App 回读已通过。共享存储回归覆盖已有网址保留名称、精确标签、备注与附件，以及元数据提交失败后的新附件回滚和重试；真实错误界面恢复与实体设备仍待验收。
- 可恢复的回收站；导入前摘要确认；schema 3 JSON / manifest 2 ZIP 交换；完整 ZIP 导出。
- 同一 Wi-Fi 配对、双向资源/附件同步、完整版本冲突选择、可选前台自动同步与断开连接；电脑端服务默认关闭。
- 原生浅色、深色与 Dynamic Type 实现；减少动态效果时取消收藏控件动画。最新可读性和窄宽度修正尚待重拍。

首次运行是空库。界面验证样例只在独立模拟器数据目录，未打包进 App，也未访问正式收藏数据。

## 安装到 iPhone

1. 使用支持 iOS 26 SDK 的 Xcode 打开 `Shiji.xcodeproj`，选择 **Shiji** scheme。
2. 在 Xcode → Settings → Accounts 登录你的 Apple 开发签名账号。真机签名和 App Group 能力取决于账号及 provisioning 配置；本项目没有携带签名身份或可直接安装的已签名 IPA。
3. 在两个 target **Shiji** / **ShijiShare** 的 Signing & Capabilities 中选择同一 Team。将 Bundle Identifier 改成你自己的唯一标识，扩展标识应以前者为前缀。
4. 在两个 target 的 App Groups 中启用同一个属于你账号的 Group，例如 `group.com.yourname.shiji`。同时把 **两个 target 的 Build Settings → SHIJI_APP_GROUP** 设为该值；Info.plist 与 entitlements 会引用它。不要只改其中一个 target。
5. 接入并信任 iPhone，根据 Xcode 提示启用开发者模式，选择设备，点击 Run。若签名提示该账号无法配置 App Groups，需要具备该能力的签名配置；不要把两个 target 分配到不同共享目录。
6. 首次打开拾集后，可在 Safari 分享菜单 → 更多中启用拾集。请在你的签名安装环境逐项验证收藏网址、文字和图片，并回到拾集确认出现。若持续空白，需保留当次扩展生命周期日志；独立模拟器的成功记录不能代替你的安装环境验收。

工程已生成，无需运行生成器。若要重新生成工程，先在 `generate_project.py` 中修改标识及 App Group 默认值，再运行 `python3 generate_project.py`；生成器会覆盖手工工程配置。

## 与电脑在同一 Wi-Fi 同步

需要配套 `desktop-app` 候选 Mac App，电脑保持运行、手机与电脑连接同一 Wi-Fi。

1. Mac App 工具栏 → **手机同步** → **开启同步**。如有多个电脑地址，选择当前 Wi-Fi 的私有 IPv4 地址，不要选择 `127.0.0.1`。
2. 点击 **生成配对码**。用 iPhone 系统相机扫描二维码并打开拾集，或点击 **复制配对码**，在 iPhone **管理 → 电脑同步** 粘贴；画廊左上角电脑图标也直达此页。二维码使用 `shiji-sync://pair` 打开配对页；没有 App 内扫码器。配对码五分钟内有效、仅可使用一次，生成新码会使旧码失效。
3. 在 iPhone 点击 **配对这台电脑**，按系统提示允许本地网络访问，再点击 **立即同步**。核对电脑名称、同步结果与上次成功时间；“已配对”表示保存了连接信息，不表示电脑此刻在线。失败信息集中在 **需要处理**，可 **重新同步**。扫码打开页面不会代替明确配对操作。
4. **App 前台自动同步**可关闭；新安装默认开启，配对后可能开始同步。开启时在 App 激活、收藏改变及前台定时检查时同步；编辑、导入或待选冲突会暂缓。退至后台停止自动调度，不提供云同步或持续后台同步；离线仍可使用本机收藏，重连后重试。
5. 出现 **选择保留的版本** 时，按 **已选择 x / y** 逐项打开比较页；版本选择在长内容之前，全部选完后点击 **同步所选版本**才提交。待选冲突期间不显示普通重新同步入口。选择作用于整个资源，包括备注、标签、授权、状态和附件归属，不逐字段拼接；同网址不同 ID 也要求选择。选择缺失版本会把另一端资源放入回收站并保留素材。

同步内容包括名称、网址、备注、完整标签、项目归属、来源授权、常用/待整理、回收站状态与本地附件。项目层级和智能集合仍由电脑管理。附件只传缺失的不可变字节，单个 64 MiB、本次传输 512 MiB 上限，校验大小、类型与 SHA-256；不会自动从网站下载封面。

连接使用 HTTPS，手机核对配对证书及私有 CA，凭据存入 Keychain。电脑 IP、证书或资源库身份改变时，在手机断开后重新生成码配对；不应绕过证书错误。无法连接时检查同一 Wi-Fi、电脑服务、本地网络权限和防火墙，再重试。

手机 **断开这台电脑**清除手机配对及同步记录、保留收藏；它不会撤销电脑端的设备授权。Mac **停止同步**暂停服务、保留配对；**解除所有手机配对**撤销所有手机令牌，之后需要重新配对，两端资源均保留。完整说明见配套桌面候选版的 `SYNC.md`。

## 备份文件交换

手机管理页 → 导入电脑备份 → 在文件 App 选 JSON / ZIP → 查看摘要 → 加入资源。完整 ZIP 带本地附件；JSON 仅元数据，导入会清除附件与封面引用。

手机管理页 → 导出完整备份 → 保存到文件 App，再传给电脑。电脑端完整恢复可能替换收藏库，应使用现有预检、确认和备份流程。

**文件导入只加入新收藏，行为不同于配对同步。** 同 ID 或同网址已有资源会跳过，手机导入不会更新其备注、标签或附件。手机仅编辑已开放的字段，保留已有未知元数据；电脑端智能集合、自动备份、预览抓取等高级功能仍由电脑版管理。手机不运行桌面 Python 服务。

手机导入总文件/解压总量上限 512 MiB，单个附件上限 64 MiB，最多 10,000 条资源。超过限额请拆分，错误不会覆盖现有收藏。ZIP 预检校验路径、大小、SHA-256 和类型；导入附件冲突不会替换已有文件。导出也会校验附件。

## 构建与验证

需要 macOS、Xcode 和对应 SDK。在本目录运行：

```sh
python3 Tests/run.py --core-only
```

这组 Foundation 测试可在解压后的独立源码包中运行，覆盖共享持久化、16 次并发采集、逗号标签、编辑冲突、回收站、JSON/ZIP、路径/校验损坏、导入取消及附件冲突。它不调用系统 Share Extension。

完整互通测试运行 `python3 Tests/run.py`，另外需要相邻 `../desktop-app` 的 Store 和 `../desktop-app/static/previews/polyhaven.jpg`。它用临时 Store 生成真实电脑压缩 ZIP，并由电脑 manifest 2 校验器读取手机导出；测试数据库均在临时目录。独立手机源码包不包含电脑版，因此默认使用 `--core-only`。

模拟器构建：

```sh
xcodebuild -project Shiji.xcodeproj -scheme Shiji -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- CODE_SIGNING_REQUIRED=NO ARCHS=arm64 build
python3 Tests/check_bundle.py build/DerivedData/Build/Products/Debug-iphonesimulator/Shiji.app
```

截至 2026-10-07，核心与 ZIP 互通测试通过，新增原生合并测试覆盖双向变更、同网址身份冲突、回收站及迟到采集保护。真实生产 Swift URLSession 客户端对临时 HTTPS 桌面服务的双向编辑/附件、明确冲突、错误证书 pin 拒绝和迟到本机采集保护均通过。桌面 Python 195 项测试通过，其中同步套件 14 项。这些测试不调用系统 Share Extension，也不证明实体手机 Wi-Fi 或相机扫码可用。

2026-10-08 界面微调的模拟器 Debug、最终未签名 iPhoneOS Release、原生核心与当前 arm64 模拟器 App Group/资产检查通过，Mac 构建及签名验证完成。完整 Python 197 项通过，含生产原生模型 HTTP 状态、Vision 稠密二维码解码及无 DNS 绑定回归。此前超时由 faulthandler 确认为监听 `0.0.0.0` 时 `HTTPServer.server_bind` 的反向 DNS 阻塞；已用 `TCPServer.server_bind` 的最小覆写绕过查询，并非证书初始化或并发构建问题。设备构建只证明编译；源码包不是已签名 IPA。

实际 QA 曾操作主 App 保存完整标签 `New, exact` 与 `Native, exact`。本轮截图显示画廊大图、来源/附件数量、详情来源授权、暗色配对及 Text Size 8 的标题/滚动/空库布局；Mac 截图来自生产组件加临时真实后端的隔离窗口，窗口未激活，不能据其灰色按钮推断激活态样式。冲突/错误完整操作、展开采集控件等仍需相应证据。系统分享→App Group→主 App 的保存链路、旧系统回退、最小手机宽度、手势、增加对比度与真机均未通过本轮验证。

设计继承与原生差异见 [docs/design-adaptation.md](docs/design-adaptation.md)。根设计规范与侧车保留电脑版身份，不将本次 iPhone 控件值写回桌面令牌。

本次新增的密度、入口和同步分组说明及截图边界见 [docs/ui-polish-2026-10-08.md](docs/ui-polish-2026-10-08.md)。

## 源码包

在本目录运行 `python3 package_source.py` 生成 `dist/Shiji-iPhone-source.zip`。它仅打包 Xcode 工程、源码、测试与文档，不含构建产物、QA 数据或正式收藏数据；不是可安装 IPA。解压后打开 `Shiji.xcodeproj`，按上述账号签名与 App Group 步骤安装候选版本。

项目位于独立候选目录 `work/mobile-app`；没有改正式服务、原运行的电脑版或正式数据。
