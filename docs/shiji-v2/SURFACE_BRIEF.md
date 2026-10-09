# SHIJI V2 — Surface Brief

日期：2026-10-08。状态：已认可的 Creative Tech Dark · Motion Studio 方向固化；设计世界以两端 DESIGN.md 为准，当前 surface 的表达与事实边界以本 brief 为准。功能和数据约束继续以各端 PRODUCT.md 为准，本文件不修改产品事实。

## 视觉权威与授权范围

- 已认可方向：**Creative Tech Dark · Motion Studio**，紫色 Hero／创意几何、荧光绿关键操作、深色真实资源画廊。
- Pinned Demo：[reference/motion-studio.html](reference/motion-studio.html)；静态布局参考：[desktop.png](reference/desktop.png)、[mobile.png](reference/mobile.png)；动作参考：[walkthrough.mp4](reference/walkthrough.mp4)。
- 实施权威：[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)、[CODEX_MASTER_PROMPT.md](CODEX_MASTER_PROMPT.md)。用户补充的 `/Users/silver/Downloads/shiji_v2_motion_studio.html` 与仓库 pinned Demo 相同；其完整动画语言属于本次实现范围。
- 用户已明确授权替换旧 light／liquid 主视觉。旧 DESIGN 中暖白、鼠尾草和全页悬浮玻璃的世界已被替换；不重新发起视觉方向选择。
- 真实功能、原始数据安全、可访问性优先于概念 Demo 的像素构图。Demo 的硬编码样例、localStorage 资源存储与模拟异步成功不进入产品业务实现。

## Surface 模式与目标

| Surface | 主模式 | 表达与目标 |
| --- | --- | --- |
| 主资源图库初始浏览 | **Experience** | 用编辑式大标题、紫色品牌舞台、荧光绿运动带和真实资源封面建立创意画廊气质，让收藏值得再次打开。 |
| 分类、搜索、项目、常用、待整理、列表／参考板 | **Operate** 为主 | 保持清晰来源、数量和筛选；以位置和状态变化帮助定位，不让品牌表演抢占操作。 |
| 快速收藏与完整编辑 | **Operate** | 先保存，再整理；明确输入、正在保存、真实完成、失败和恢复。 |
| 详情、授权、附件、备注、批量操作 | **Operate** | 信息可读、动作可发现，保留原有编辑保护与恢复路径。 |
| 同步、导入／备份、恢复、回收站、扩展配对 | **Operate** | 系统结构、真实状态和确认文字优先；品牌只进入配色与有限反馈。 |

这里的模式是 surface 的表达取舍，不是新增功能、导航项或数据库字段。主图库保留完整真实浏览能力；管理入口不因概念稿没有展示而消失。

## 当前表达

桌面／Web 主图库在 `scope=all`、`view=grid` 且没有有效过滤条件时显示 Hero 和 ticker；筛选计数配置 `tagMode`／`includeSubdomains` 本身不使 Hero 隐藏。Hero 是当前主图库表达，不能推广成所有管理页的强制组成。

宽屏为侧栏、编辑式 Hero 和稳定双列画廊；在 1279px 及以下侧栏抽出，760px 及以下 Hero 堆叠，480px 及以下真实图库一列。画廊实际保留 `data-gallery-columns="2"`、每次 60 条继续浏览、完整匹配范围和 keyed 节点。参考图的多列拼贴或固定样例数量不覆盖这些契约。

iPhone 使用原生 NavigationStack + 三项 TabView、系统搜索与单列 LazyVStack。初始“全部”浏览且没有搜索、分类或范围限制时显示品牌 Hero；无障碍字号省略 Hero，让触控和内容优先。浅色、深色、跟随系统和 Studio／Calm 是独立 UI 偏好，不写入资源内容。系统 Form、List、QuickLook、文件选取和同步页保留原生结构。

## 三类真实资源

| 呈现 | 真实映射 | 内容策略 |
| --- | --- | --- |
| Visual | 除 Tool／Text 外的现有资源 | 真实可用封面优先；缺封面显示域名／类型占位，不补造作品或许可证。 |
| Tool | `kind=website` 且 `category=开发工具` | 强调真实工具名称、域名和介绍；有真实封面时仍可显示。 |
| Text | `kind=code` 或 `kind=prompt` | 显示实际代码／提示词摘要，保持文字可读；不以装饰封面代替内容。 |

网页 `ShijiV2.cardType` 与 iPhone `Resource.presentation` 从现有字段派生；不新增序列化类型，不改变 schema 3 或 manifest 2。真实卡片不得混入 pinned Demo 的 seed 内容。

## Motion 与所有权

Motion Studio 是明确选择的强表达模式，Calm 是精简模式。网页偏好键为 `shiji-v2-motion-mode`，系统 `prefers-reduced-motion` 优先；原生读取 `accessibilityReduceMotion`，iPhone 还读取同名 AppStorage 偏好。macOS 原生 dock 通过校验来源的 `libraryMotion` bridge 接收网页有效 Calm 状态，并同时遵守原生系统 Reduce Motion。

`ShijiBits` 是真实卡片布局 FLIP 与图片 tilt 的唯一 owner；`ShijiCards` 保持资源 ID 节点、图片解码复用及可用焦点；`ShijiGlass` 只维护分类指示器；`ShijiMotion` 编排品牌、搜索、详情代理与保存反馈。Studio 已在 Bits 内扩展 680ms FLIP、850ms blur enter 和 500ms exit ghost（最多 9 个可见代理）；不能给实际卡片叠加第二套 transform。Hover 表达只在精细鼠标条件下启用，键盘、触摸、完整图片预览与破图有回退。

网页装饰循环受 Studio／Calm／系统偏好、页面可见性、舞台可见性和弹层状态控制。网页临时 curtain、stamp、ghost、飞入与粒子不拥有点击或焦点；取消、关闭、模式变化和销毁时清理。实际详情、搜索输入与保存结果不等待装饰完成。最终实现参数保存在两端 sidecar 的 `extensions.motion`。网页包含品牌幕布／重播、受控几何与 ticker 循环、stamp、指针聚光／sheen、分类 pill／count、模态／详情 stagger、保存飞入／burst 和真实常用反馈。iPhone 原生实现幕布／重播、按 Calm／系统减少动态／scene／可见性暂停的 Timeline 几何、NativeMotionReveal、分类 stamp、保存飞入／burst 与真实常用 burst，同时保留系统 spring／zoom 和平台导航。

## Persist-first 收藏

快速收藏调用真实已有保存入口；持久化成功之后才显示“已收藏”、保存飞入、15 粒子的成功 burst 或卡片高亮。网页分类／主要控件点击的 6 粒子是通用动作微反馈，不表达“已保存”；设为常用的 6 粒子由成功写入事件触发。失败保留网址／草稿并提供恢复；重复收藏遵守真实去重语义，不以动画掩盖重复或失败。网页后续元数据补全使用安全请求和受保护字段回填，不能覆盖用户修改或把补全等待伪装成保存失败。

iPhone 的网址保存先 `files.save`，然后重新载入、更新 captureSequence、关闭编辑并显示可访问的完成反馈；不依赖电脑在线。新增文件路径刷新本地库，但目前不递增同一网址反馈计数，不能声称全部输入方式已有相同动画。

## 材质与平台边界

网页阅读区和采集层是实色暗平面；CSS 不等于原生 Liquid Glass。macOS 26 / iOS 26 的原生收藏层使用系统 glassEffect，较早系统保留 regularMaterial 的源码回退。原生导航、触控目标、动态字体与系统模态保留，品牌表达不重写平台结构。

## 已有证据与可声明范围

下表是现有 QA 产物的用途索引，不表示本次文档过程新增了验收。本次固化仅阅读源码与已有截图，不重新执行设计审查或功能测试。

| 证据 | 可支持的观察 |
| --- | --- |
| [p5-web-desktop.png](evidence/p5-web-desktop.png) | 实际网页宽屏暗色首屏、紫色 Hero、荧光绿操作和保留的工作台。 |
| [p5-gallery.png](evidence/p5-gallery.png) | 真实资源画廊、无封面域名占位、Text 摘要、长名称与准确标签。 |
| [p5-web-mobile.png](evidence/p5-web-mobile.png) | 网页窄屏的堆叠 Hero、搜索与收藏入口；仅支持网页 surface。 |
| [p5-native-mac-active.png](evidence/p5-native-mac-active.png) / [p5-native-mac-expanded.png](evidence/p5-native-mac-expanded.png) | macOS 前台窗口中的原生收藏层收起／展开状态。 |
| [p3-iphone-dark.png](evidence/p3-iphone-dark.png) | 已有 agent-owned `Shiji iPhone QA` 模拟器上的原生深色画廊；不是实际手机。 |
| [p5-iphone-light.png](evidence/p5-iphone-light.png) | 原生浅色图库与语义 tint。 |
| [p5-iphone-large-type.png](evidence/p5-iphone-large-type.png) | 原生大字号／系统减少动态场景，内容与收藏入口的适配。 |
| [p5-iphone-detail.png](evidence/p5-iphone-detail.png) | 原生详情、来源与授权、编辑操作。 |

早期截图呈现的是其捕获时刻的静态外观，不足以证明后续补齐的全部动画。新增实现的捕获状态如下；运行检查与真实测试结果仍以 [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) 为准，不从静态截图推断整个动画时序或全矩阵通过。

| 新增证据 | 捕获内容与边界 |
| --- | --- |
| [motion-desktop.png](evidence/motion-desktop.png) / [motion-web-mobile.png](evidence/motion-web-mobile.png) | 完整几何语言在桌面／窄屏网页的外观。 |
| [motion-category.png](evidence/motion-category.png) | 分类 stamp 与卡片进退的瞬间。 |
| [motion-capture-flight.png](evidence/motion-capture-flight.png) | 真实新增收藏后的网页飞入瞬间与完成文字。 |
| [motion-calm.png](evidence/motion-calm.png) | Calm 的可读静态状态；单张截图不能证明停止时序。 |
| [motion-iphone-studio.png](evidence/motion-iphone-studio.png) | 原生 iPhone QA 的 Studio 几何与重播入口。 |
| [motion-iphone-interaction.mp4](evidence/motion-iphone-interaction.mp4) | 18 秒真实操作裁切，包含品牌重播与分类变化；不声称此录屏捕获了 iPhone 保存飞入。 |

## 保留的限制

- Share Extension 持续空白页尚未修复；视觉升级不构成系统分享端到端成功。
- macOS inactive-window 玻璃状态尚未实际验证；现有截图支持前台窗口。
- 不同 iPhone 机型、真实手机和旧 OS fallback 没有运行验收；源码可用性判断不等于实际测试。
- 现有截图不代表全部 VoiceOver、对比度、性能或设备矩阵已通过。
- PRODUCT.md 的能力与约束保持原样；完整安装、分发、配对和业务限制不由本视觉文档重新承诺。


## Desktop card restoration addendum · 2026-10-09

依据用户本轮明确要求，桌面卡片采用三列基准、真实技术字段决定的两列特色 Tool 卡和八类派生海报封面，替换上文旧的双列／域名占位契约。分页、稳定 ID、完整数据筛选与真实封面优先仍保留；首页大尺寸 Hero 和全部品牌动画完全保留。原生 iPhone 当前呈现不变。实际代码、对比截图和验收边界见 [card-restoration/REPORT.md](card-restoration/REPORT.md)。


Card tactile follow-up: move the entire cover/title/metadata surface under the existing ShijiBits pointer owner. Bounded mouse-only elastic pickup/release, stable outer card FLIP and IDs, drag/click arbitration, interruptible cancellation. Preserve the complete Hero, Calm, reduced motion and native touch scrolling. No persisted drag ordering.


## Cover Studio 2.0 · 2026-10-09

The desktop gallery remains an Experience surface inside the existing local resource app. Retain the entire approved Hero, brand stage, stable masonry/featured footprints and Bits tactile interaction. Replace only the automatic cover art direction with saved semantics → stable structural variant → independent coordinated palette. Actual covers remain first. Use local glyph-aware typography, intentional safe zones and real code/excerpts instead of uniform placeholders or invented metadata. P0–P3 provide 24 static poster structures / nine palettes and a runnable temporary-data comparison. Internal spatial motion and custom persistence await the user's art-quality confirmation; see [Cover Studio report](../cover-studio-2/REPORT.md).
