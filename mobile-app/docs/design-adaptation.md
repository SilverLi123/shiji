# 拾集 iPhone：现有设计的原生适配

本文件记录现有「清晰画廊上的采集层」在 iPhone 的实现差异与验证边界。`DESIGN.md` 和 `.impeccable/design.json` 保留原始桌面/浏览器规范，内容未改写；本文件不建立第二套全局令牌。产品范围来自 `PRODUCT.md`，具体屏幕约束来自 `docs/mobile-surface.md`。这是对既有视觉世界的原生扩展，没有另选风格或原生像素稿；HTML/CSS detector 不适用于 SwiftUI，已跳过。

## Overview

大图、真实资源名称、来源与授权仍是阅读重心。鼠尾草操作色、中文文案、无磨砂的内容平面沿用既有身份。手机使用离线 JSON / App Group 收藏库；用户已确认优先实现同 Wi-Fi 手机↔电脑同步。配对后双向同步资源和附件，可选前台自动同步，不提供云服务或持续后台运行。原有 schema 3 JSON / manifest 2 ZIP 导入保持只加新记录、跳过已有资源的行为；手机不自动联网抓取封面。

界面验证素材属于独立 QA 模拟器，不随 App 或源码包出货，不代表真实收藏或授权。AppIcon 为 `Tests/make_icon.swift` 用 CoreGraphics 绘制的原创几何书签，PNG 内嵌来源与生成说明；没有引入第三方图像。

## Colors

| 既有角色 | iPhone 适配 | 原因与边界 |
| --- | --- | --- |
| 鼠尾草深绿 accent `#325a4a` | Asset Catalog 浅色 sRGB `(0.196, 0.353, 0.290)`，深色 `(0.573, 0.737, 0.624)` | 保留浅色身份，用不透明浅鼠尾草适配 Dark Mode；系统 tint 作用于动作与选中态。 |
| 暖白纸面、深绿墨色 | `systemGroupedBackground`、`secondarySystemGroupedBackground`、primary 等系统语义角色 | 原生浅深色表面替代桌面固定纸面色，未把 Dark Mode 反推到桌面规范。 |
| 辅助叶灰绿 | `NativePalette.secondaryText`：浅色 RGB `(0.325, 0.388, 0.361)`、深色 `(0.682, 0.737, 0.710)`，alpha 1 | 修正原生系统 secondary 在现有浅色画廊中偏淡的问题；源值已修改，实际屏幕对比度需重拍确认。 |
| 主按钮前景 | `NativePalette.onAccent`：浅色 white、深色 RGB `(0.090, 0.141, 0.106)` | 深色系统突出按钮呈浅鼠尾草，改用深色前景；不可继续套用桌面「所有 accent 按钮白字」的固定规则。效果待验证。 |
| 授权待确认 | 原生 yellow opacity 0.2 胶囊 | 空许可与明确「待确认」采用同一提示；颜色表示待确认，不推断资源可商用。 |

浏览器 `glass-fill`、`capture-fill` 和 CSS 投影不参与 iPhone 原生材质。macOS `native-capture-ink` 与白色 tint 的组合也没有直接复制到手机。手机 glass 由系统根据原生上下文渲染，源码没有把桌面 CSS 的颜色、模糊或边缘参数伪装成 Liquid Glass。

## Typography

手机使用 SwiftUI 系统语义字体：导航大标题，资源 `.title3` semibold，详情 `.title2` semibold，正文/body、subheadline、caption 与 footnote。字号由 Dynamic Type 缩放，不把桌面 34/18/16/14/13/12px 层级固定为手机 pt。长资源标题自然换行；辅助域名单行、描述最多两行是画廊密度选择，完整信息由详情承接。

标签输入以回车提交完整字符串，逗号保留在名称中。实际主 App QA 曾保存 `New, exact` 与 `Native, exact`；这项证据不等于系统分享保存链路已通过。

## Layout

`NavigationStack`、三项 `TabView`（资源库 / 集合 / 管理）、系统搜索、菜单、Form、文件选取和 QuickLook 取代桌面侧栏、抽屉和网页工具。画廊为单列 `LazyVStack`，横向分类自身滚动；内容水平内边距 20pt，资源间距 24pt。画廊封面高 220pt，详情封面高 240pt。图像 scaled-to-fill 适配预览框并裁切，保持清晰；完整附件预览交给 QuickLook，不宣称画廊框展示整个原图。

采集入口放在底部安全区内，详情编辑动作由 bottom safe-area inset 承接。分类和详情附件动作显式提供 44pt 最小高度；采集动作 48pt。系统控件继续使用平台布局。最小支持手机宽度、硬件姿态和边缘返回手势尚无运行证据，不能由这些源码值推断全设备合格。

## Elevation & Depth

实际资源与正文保持清晰平置，没有整卡玻璃、额外悬停投影或装饰循环。iOS 26+ 的采集操作使用一个 `GlassEffectContainer`、交互式 `.glassEffect` 与稳定 `glassEffectID`。点击「收藏」展开「网址 / 素材 / 收起」，动作完成后收起；这是同一控制层内的状态变化。

辅助功能字号直接使用系统菜单。正常字号下 `ViewThatFits(in: .horizontal)` 尝试保持 icon 与标签的完整一行布局，空间不足时切换菜单；iOS 17–25 同样使用 `.regularMaterial` 菜单回退。`accessibilityReduceMotion` 为 true 时取消 spring，否则使用 response 0.38、dampingFraction 0.82。旧系统与 Reduce Motion 实际效果仍待验证；没有手工复制浏览器阴影，也没有自定义整页透明背景。

## Shapes

封面沿用 14pt 柔和圆角，整张资源没有新卡片底板。分类与采集是局部胶囊，关闭动作为圆形。编辑、管理、导入摘要使用系统 Form/List/sheet 转角和分组，避免把桌面工具面板 22/24px 半径铺到全部手机表面。

## Components

来源、作者、许可与授权链接保持详情中的完整分组。编辑有未保存退出确认、冲突提示与保留草稿的保存失败反馈。回收站只标记删除，可恢复。导入先显示摘要、确认后协调读取并合并；取消不写库，既有记录不被覆盖，附件冲突拒绝并回滚新写入载荷。上述数据行为有核心测试支持，文件选择/系统分享/手势等原生入口不能由核心测试替代。

Share Extension 已有原生 loading、字段、取消、保存、错误与保留草稿后重试的源码，并设计为读取网址、文字或单张图片。实际系统入口仍是持续空白页，当前未能操作这些控件或完成扩展→主 App 验证；它是未解决的功能缺陷。最新版本增加控制器加载、表单渲染、provider 数量与可见尺寸的 OSLog，等待真实重新调用后诊断。旧系统日志证明控制器类被实例化并读取 provider，不支持把根因直接归为类名或 debug-dylib 配置。

### 同 Wi-Fi 同步

`App/ComputerSync.swift` 延续系统 Form、NavigationLink、语义字体及现有 `NativePalette.secondaryText`：管理页进入电脑同步，分组显示电脑/结果、配对输入、手动动作、前台开关、冲突和断开。冲突比较采用完整资源的手机/电脑分组及明确选择，全部选择后才提交；错误与等待有文字状态。扫码通过系统相机和 `shiji-sync://pair` 打开配对页，仍需点击配对，不新增装饰性扫码面板或玻璃背景。

桌面候选 `desktop/PhoneSync.swift` 为原生工具 sheet：默认关闭的服务、Wi-Fi 地址选择、一次性 QR/复制、已配对设备及停止/撤销。它复用既有系统字形、分组间距和普通语义表面，没有改画廊或全局令牌。基于源码，这两个操作面符合既有内容平面与功能操作层的分工；原生同步页尚无已接受截图，不能据源码认证可读性、Dynamic Type、二维码识别、权限弹窗或实际操作完成。

配对客户端使用 HTTPS、精确证书 pin、私有 CA 独立验证和 Keychain；三方快照比较处理并发变更，手机协调读写/电脑事务检查阻止覆盖迟到采集。该行为与「准确内容、明确状态、可恢复操作」的既有原则一致，不把安全配置值变成视觉装饰。前台自动同步默认开启但可关闭；App 后台停止调度，冲突/编辑/导入暂缓。手机断开、桌面停止与撤销都有保留资源的边界。

## 既有桌面文档差异

本次扫描发现的以下差异存在于既有桌面规范/侧车/实现之间，不是手机适配引起，也未在本次修订：

| 差异 | 现有证据 | 本次处理 |
| --- | --- | --- |
| 侧栏组件宽度 | DESIGN Layout 与桌面 `static/liquid-glass.css` 为 226px，侧车 `Sidebar Navigation` 预览为 220px | 保留原文件；组件预览不是手机或桌面整页尺寸证据。 |
| focus 变量与可见轮廓 | 桌面 CSS 的 `--focus` 为 `#325a4a`，全局 `:focus-visible` 与 DESIGN 的 `focus-ring` 为 `#52715a` | 记录别名/实现差异，不统一或覆盖桌面值。 |
| 搜索聚焦局部色 | CSS/侧车搜索底线使用 `#526b58`、聚焦底色 `#e6eee5`，不属于 DESIGN frontmatter 中的命名原语 | 记录已有组件局部常量，不补造手机全局令牌。 |
| 平台特定内容 | 侧车只含独立 HTML/CSS 组件；DESIGN 包含桌面断点、浏览器阴影、macOS tint 与配对面板 | 不将它们当作 iPhone 的渲染契约，也不为手机改写现有文档。 |

## 验证状态（2026-10-07）

`build/core-tests.log` 记录核心与真实电脑 ZIP 互通通过，包括 16 次并发采集、完整逗号标签、冲突、可恢复回收站、取消/损坏/路径/校验/附件冲突及 PDF/文字载荷。新增 `build/sync-core-latest.log` 合并测试通过；`build/sync-integration.log` 记录生产 Swift URLSession 对临时 HTTPS 服务的双向编辑/附件、明确冲突、错误证书拒绝及迟到采集保护通过。桌面 `build/full-python-tests.log` 的 195 项及 `build/sync-tests.log` 的 14 项通过。本次 `sync-ios-build.log` / `sync-ios-release.log` 均为 `BUILD SUCCEEDED`；桌面 `sync-macos-build.log` 记录构建脚本完成编译、ad-hoc 签名与打包。此前资产检查通过，最新产物安装与原生 UI 仍待验收。设备构建未签名；没有签名 IPA、实体手机 Wi-Fi/安装或 production provisioning 结论。

`.impeccable/review/iphone-light.jpg`、`iphone-dark.jpg`、`iphone-dynamic-type.jpg`、`iphone-detail.jpg`、`iphone-share.jpg` 是实际 iPhone 17 / iOS 27 独立 QA 模拟器截图；辅助功能截图报告为 size 8 / accessibilityLarge。它们来自此次标签/前景修正之前的版本。分享截图中的空白页持续超过 90 秒，进程存活，是稳定失败证据。独立 `build/finish-review.md` 的 disposition 为 `fix`。

待复审：实际同步配对/冲突页、扫码入口、网络权限与断开操作；重拍展开的暗色采集控件、浅色辅助信息与详情按钮；运行最小手机宽度回退；真实系统分享取消/保存与主 App 可见链路。此前验收受 Mac 锁定及 `noWindowsAvailable` 设备输入失败阻塞，目前仍在尝试原生采集，尚无新截图可用于通过判定。原有分享空白未解决；旧系统回退、增加对比度、手势、材质动态效果及真机均未验证。协议测试与文档完成不改变这些待修复/待验证状态。
