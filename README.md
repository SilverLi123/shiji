# 拾集 · Shiji

用于收藏和管理开发资源的本地工具：网站、美术素材、设计参考、音频、视频、代码与灵感。包含 macOS App、Chrome / Edge 浏览器采集扩展和原生 iPhone App；手机和电脑可通过同一 Wi-Fi 配对同步。

当前候选进入 **SHIJI V6 Smart Capture Engine**，基于 Next／V5.2，保留已认可的 V5 Spatial Poster。已实现先保存后补全、持久后台任务、租约恢复、真实封面校验和需确认的整理建议；实现、兼容性、245 项 Python／53 组 Node、强杀恢复及实际界面证据见 [V6 交付报告](docs/shiji-v6-capture/REPORT.md)。本候选尚未推送／合入 main，原生任务面板、安装后扩展和实体 iPhone 仍有验收项目。原生首次详情长帧沿用 [V5.2 调查](docs/shiji-v5.2/REPORT.md)，不因本轮功能通过而标记已修复。既有分享专项背景见 [Next 审查](docs/shiji-next/BASELINE_AUDIT.md)。

## 代码结构

- `desktop-app/`：Python 本地服务、资源管理网页、SwiftUI macOS 窗口及测试。
- `desktop-app/browser-extension/`：Manifest V3 扩展，主动收藏网页、选中文字、图片、链接和可见区域截图。
- `mobile-app/`：SwiftUI iPhone 工程、共享持久化、分享扩展源码和测试。

个人收藏、附件数据、配对凭据、证书、构建产物和临时验收记录均不进入仓库。首次启动创建自己的空资源库。SQLite schema 3 / ZIP manifest 2 保持兼容。

## 运行桌面端

需要 macOS、Python 3.9+；构建原生 App 还需要 Xcode / Swift SDK。没有第三方运行时依赖。

```sh
cd desktop-app
python3 desktop/build.py
open 'dist/Dev Resource Library.app'
```

App 默认使用本机 `8782` 端口，数据保存在 `~/Library/Application Support/DevResourceLibrary`。浏览器扩展可从 App 打开文件夹，也可在 `chrome://extensions/` 或 `edge://extensions/` 中开启开发者模式并加载 `desktop-app/browser-extension/`。

完整安装、旧收藏迁移和采集配对说明见 [桌面端说明](desktop-app/APP.md)。

## 运行 iPhone 端

使用支持 iOS 26 SDK 的 Xcode 打开 `mobile-app/Shiji.xcodeproj`，选择 **Shiji** scheme。最低运行系统为 iOS 17。真机运行需配置自己的 Apple Team、唯一 Bundle Identifier，以及 App / Share Extension 一致的 App Group；仓库不提供已签名 IPA。

详细步骤见 [iPhone 说明](mobile-app/README.md)。

## 同一 Wi-Fi 同步

在 Mac App 的“手机同步”中开启服务并生成配对码，在 iPhone“管理 → 电脑同步”确认配对。支持双向同步收藏、备注、标签、状态和本地附件；两端同时修改的资源需要明确选择版本。服务默认关闭，采用 HTTPS 和证书校验，手机凭据保存在 Keychain；没有云账号或持续后台同步。

详细配置、冲突处理和排错见 [同步说明](desktop-app/SYNC.md)。

## 验证

Python 测试使用临时数据目录；原生模型与二维码测试需要 macOS / Xcode。前端 DOM 测试使用开发依赖 jsdom（已在 Node.js 24 验证），不参与 App 运行。

```sh
cd desktop-app
npm ci --ignore-scripts --no-audit --no-fund
python3 -m unittest discover -s tests
npm test
```

手机核心、桌面 ZIP 互通与真实 HTTPS 同步集成：

```sh
cd mobile-app
python3 Tests/run.py
python3 Tests/sync_integration.py
```

2026-10-10 V5.1 最终本地验证：208 项 Python、52 组 Node、Swift 核心与 ZIP 互通、实际 HTTPS 同步检查通过，macOS 候选构建成功。具体原始日志、实测数据和未完成验收见当前报告；本轮没有推送或新的远端 CI 结果。自动化使用临时数据，覆盖 schema 3 / manifest 2；它不证明真机系统分享或完整 UI 性能通过。

## 当前边界

- iPhone 系统分享扩展在 QA 模拟器中仍有空白页问题；App 内收藏可用，系统分享保存链路尚未通过。
- 实体 iPhone 的签名安装、Wi-Fi 同步和相机扫码仍需真机验证。
- 浏览器扩展需要手动加载，尚未发布到扩展商店；Mac App 是未公证的开发构建。
- 暂不支持 Windows、Safari 扩展或云同步。

设计及第三方来源说明见各端 `DESIGN.md` 和 [THIRD-PARTY.md](desktop-app/THIRD-PARTY.md)。
