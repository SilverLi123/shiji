---
name: "拾集 SHIJI V2 · Desktop Motion Studio"
description: "深色创意画廊，以紫色品牌几何和荧光绿操作连接真实收藏。"
colors:
  shiji-bg: "#0c0d10"
  shiji-sidebar: "#101115"
  shiji-surface: "#15171d"
  shiji-surface-raised: "#1d2027"
  shiji-fg: "#f5f5f3"
  shiji-muted: "#90919c"
  shiji-line: "rgba(255,255,255,.095)"
  shiji-lime: "#d7ff65"
  accent-hover: "#e5ff9d"
  accent-soft: "#252c18"
  shiji-violet: "#a58cff"
  shiji-cyan: "#79dfff"
  brand-wash: "#e5ccff"
  brand-gradient-start: "#a991f6"
  brand-gradient-end: "#8260e1"
  intro-symbol: "#835cf4"
  feedback-coral: "#ff9d87"
  control-muted: "#b5b6be"
  control-hover: "#292d34"
  field-stroke: "#424650"
  cover-oat: "#f0ece3"
  cover-yellow: "#ffd954"
  cover-coral: "#f5b8a9"
  cover-blue: "#171b36"
  tool-preview: "#181e17"
  text-preview: "#191b27"
  text-preview-ink: "#c5b7ff"
  error-fill: "#332321"
  error-ink: "#ffb2aa"
  error-stroke: "#734a45"
  pending-license-fill: "#433918"
  pending-license-ink: "#ffe395"
typography:
  display:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "clamp(40px,4.5vw,64px)"
    fontWeight: 850
    lineHeight: 1.2
    letterSpacing: "-.035em"
  intro:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "clamp(95px,16vw,245px)"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-.04em"
  headline:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "28px"
    fontWeight: 750
    lineHeight: 1.25
    letterSpacing: "-.025em"
  title:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "19px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "-.015em"
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "16px"
    lineHeight: 1.6
  control:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "14px"
    fontWeight: 700
  description:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "13px"
    lineHeight: 1.6
  label:
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif'
    fontSize: "11px"
rounded:
  control: "8px"
  brand-mark: "9px"
  preview: "12px"
  stage: "16px"
  pill: "99px"
  tag: "999px"
spacing:
  small: "8px"
  control-gap: "12px"
  medium: "16px"
  compact-gallery-gap: "18px"
  panel: "20px"
  gallery-gap: "22px"
  section: "24px"
  narrow-workspace: "28px"
  workspace-inline: "36px"
components:
  button-primary:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "{colors.shiji-bg}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-hero:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "{colors.shiji-bg}"
    rounded: "{rounded.pill}"
    padding: "12px 20px"
  button-secondary:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  search-field:
    backgroundColor: "{colors.shiji-surface}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.control}"
    padding: "0 12px"
  navigation-active:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-lime}"
    rounded: "{rounded.control}"
    padding: "9px 12px"
  category-active:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "{colors.shiji-bg}"
    rounded: "{rounded.pill}"
    padding: "7px 12px"
  tag:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.control-muted}"
    rounded: "{rounded.tag}"
    padding: "6px 12px"
  resource-metadata:
    textColor: "{colors.shiji-fg}"
    typography: "{typography.title}"
    padding: "16px 0 0"
  form-field:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  browser-capture-deck:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.pill}"
    padding: "6px"
---

# Design System: 拾集 SHIJI V2 · Desktop Motion Studio

## Overview

**Creative North Star: "Creative Tech Dark · Motion Studio"**

拾集把真实收藏放进深色创意画廊：荧光绿指出可以执行的动作，紫色几何舞台承载品牌，低边框的内容平面保持图片、工具来源和文本摘要清晰。排版有编辑式的大标题，也保留技术工作台的信息秩序。

本文件固化已经认可并实现的 SHIJI V2 世界，替换旧的暖白／鼠尾草／整页玻璃方向。视觉权威是 `../docs/shiji-v2/IMPLEMENTATION_PLAN.md`、`CODEX_MASTER_PROMPT.md` 与 `reference/motion-studio.html`；实际令牌从 `static/shiji-v2.css` 及其保留的基础层提取。网页管理区仍由 WKWebView 承载，原生 macOS 操作使用独立的系统材料；两者共享品牌，保留各自平台结构。

**Key Characteristics:**
- 深色内容平面、紫色品牌舞台、荧光绿关键操作
- Visual / Tool / Text 三类真实资源表达
- 编辑式标题与紧凑、清楚的管理控件
- Studio / Calm 与系统减少动态效果共同控制动效
- 原生操作材料和网页不透明阅读层各自承担职责

## Colors

frontmatter 是规范值。`static/shiji-v2.css` 最后加载，覆盖旧主题；底层文件仍承担未被替换的布局和控件规则，不能重新把旧浅色令牌当作当前视觉权威。

### Primary

**荧光绿**（shiji-lime）用于主要收藏操作、分类选择、焦点、常用状态与品牌几何；accent-hover 是主要按钮悬停。深色字（shiji-bg）落在绿底上。accent-soft 是源码保留的品牌暗底令牌。

### Secondary

**创意紫**（shiji-violet）用于品牌舞台底色；最终舞台叠加 brand-gradient-start／brand-gradient-end 的斜向渐变与 brand-wash 的指针聚光。intro-symbol 是幕布字标中的紫色符号。文本型卡片采用独立的 text-preview 与 text-preview-ink，保持代码／提示词摘要可读。

### Tertiary

**技术青**（shiji-cyan）和 **反馈珊瑚**（feedback-coral）与绿／紫共同组成短暂粒子反馈；当前主要控件与链接仍以荧光绿为强调，不据此臆造整套青色状态。

### Neutral

**画廊黑、侧栏黑、操作平面与抬升平面**（shiji-bg、shiji-sidebar、shiji-surface、shiji-surface-raised）提供层次。shiji-fg 是主要文字，shiji-muted 是说明／来源，control-muted 用于次要操作与标签，shiji-line 是精细边界。field-stroke 提供输入边界，control-hover 提供普通控件悬停。

工具占位使用 tool-preview。保存错误使用 error-fill／error-ink／error-stroke；授权待确认使用 pending-license-fill／pending-license-ink，仍以文字明确说明状态。高对比度系统偏好提升次级文字与边界，具体值记录在 sidecar。

**The Accent Restraint Rule.** 荧光绿集中于主要操作、选择和必要反馈；图片颜色与紫色舞台保留自己的表达空间。

## Typography

**Display / Body Font:** 系统与中文字体栈，见 frontmatter；没有远程字体依赖。macOS 原生搜索、配对与采集控件使用 SwiftUI 系统字体，网页字号不直接移植到原生控件。

大标题紧凑而有力度，正文保持中性。display 用于主图库的品牌标题；headline 用于资源区域；title 用于真实资源名称；body 是浏览器基础文本，description 用于卡片介绍，label 用于域名／分类等辅助信息。Hero 说明单独使用较舒展的行高（1.9），文本卡片摘要使用行高（1.7）。

网页 Hero 在中宽屏改为 `clamp(40px,6vw,60px)`，窄屏为（48px），最窄分支为（44px）；区域标题依次降至（24px／22px）。图库卡片标题在最窄分支为（20px），不随 Hero 一同缩小。小号英文工作台标签是辅助层；资源名称、错误与保存状态不得仅以微型英文标签表达。

## Layout

完整侧栏宽（238px）；主工作区最大宽（1500px），宽屏内边距为（34px 36px 110px）。顶部栏贴住页面顶边，无旧版悬浮玻璃卡片外观。图库采用 `data-gallery-columns="3"`：视口大于 900px 为三列，481–900px 为两列，480px 以下一列。保存了非空 `language` 技术字段的 Tool 卡在三列、舒适密度、构图预览中跨两列；由真实资源字段决定，不按列表序号、常用状态或筛选结果重新挑选。紧凑密度、完整图片预览与窄屏保持统一列宽。ShijiBits 在同一写宽／读高／写位置／读矩形批次计算连续列跨度，仍保留 keyed ID 与每次 60 条追加。

在（1279px）及以下，侧栏成为可抽出的固定导航，宽（260px），工作区内边距变为（28px 24px 110px）。在（760px）及以下，Hero 上下排列，分类横向滚动，工具条换行；工作区使用（24px 20px 110px）。在（480px）及以下，工作区使用（22px 16px 110px），搜索独占一行，列表与详情内容允许换行。

Hero 的具体出现条件、首屏叙事和不同任务模式见 `../docs/shiji-v2/SURFACE_BRIEF.md`。列表、参考板、搜索、筛选、选择与管理入口保持既有结构和真实数据范围，不能以概念稿的固定卡片网格替换。

## Elevation & Depth

内容默认平置，卡片无外框、无卡片阴影；深度主要由暗色平面的亮度差提供。浮出的工具、详情、对话框和保存反馈使用局部阴影。浏览器采集层使用实色暗底，`backdrop-filter` 已关闭；macOS 26 的采集胶囊使用真实 `.glassEffect(.regular.interactive())`，较早 macOS 使用 `.regularMaterial`。

### Shadow Vocabulary

- 工具面板：`0 16px 40px #0006`，只承接展开操作。
- 详情抽屉：`-16px 0 50px #0008`，强调右侧层级。
- 对话框：`0 24px 80px #0009`，用于聚焦任务。
- 采集层：`0 8px 32px #0006`；Toast：`0 10px 30px #0006`。

**The Material Boundary Rule.** 原生系统材料属于原生操作层；网页 CSS 与暗色阅读平面不得被称为原生 Liquid Glass。

动效模式以网页偏好 `shiji-v2-motion-mode` 保存；系统 `prefers-reduced-motion` 优先。品牌循环在后台、舞台不可见、详情或对话框打开时暂停。减少透明度使用实色平面。具体动效参数由 `.impeccable/design.json` 记录，业务保存与内容可交互不能等待装饰结束。首次／重播幕布（1370ms）包含品牌字（800ms）和延迟进入的标题；可跳过，Esc 也会取消。品牌书签、轨道、网格、cutout、tracer、spark、模式 beacon 与 ticker 形成受控循环，不绕过暂停条件。

## Shapes

控件使用紧凑圆角，预览使用中等圆角，品牌舞台与对话框使用更宽松圆角，值在 frontmatter。分类、标签与收藏入口使用胶囊；品牌书签是带缺口的几何形，不是内容封面。资源信息本身无额外圆角容器。详情宽屏保留左侧圆角，手机网页分支成为直角全宽面。

## Components

### Buttons

主要按钮以荧光绿底和画廊黑文字表达动作；默认按钮最小高度（42px），Hero 使用胶囊轮廓。次要按钮使用抬升平面与精细边界；文本操作保持次级文字。键盘焦点为绿色外轮廓（2px）与偏移（4px），禁用状态保留真实不可用语义，不依赖颜色。

### Inputs / Fields

搜索字段为暗底圆角，输入字号（13px）；焦点扩大搜索区域并出现绿色底线，Esc 返回来源焦点。表单字段用抬升平面、field-stroke 边界与规范内边距；Quick Capture 的网址输入独立使用（16px）文字和（15px）内边距。错误在输入附近显示可恢复说明，失败保留草稿。

### Navigation / Chips

侧栏当前项为抬升平面与荧光绿文字，最小高度沿用（40px）。分类是有数量的可横向滚动胶囊；选中底色为荧光绿，文字为画廊黑。`liquid-glass.js` 仅维护分类指示器，不拥有卡片布局。标签保留准确名称，包括逗号；过滤条件可移除，不能为视觉省略“筛选／显示／选择”入口。

### Cards / Containers

Visual 优先真实可用封面；Tool 对应 `kind=website` 且分类为“开发工具”；Text 对应 `kind=code/prompt`，呈现实际摘要。缺封面显示域名／类型识别，不虚构作品。卡片标题、来源、介绍、标签与附件来自资源记录；列表与参考板沿用同一真实记录。

**The Single Motion Owner Rule.** `ShijiBits` 独占资源卡片 FLIP 与整卡 pointer pose；编排层不得在同一实际节点上叠加第二套 transform。

### Capture / Detail

网页采集胶囊与 macOS 原生采集胶囊是两种实现。原生展开使用 `GlassEffectContainer(spacing:16)`、内部间距（12pt），图标按钮为（46×46pt），文字为系统半粗（14pt）；宿主固定深色外观。原生展开同时遵守系统 Reduce Motion 与 `libraryMotion` bridge 传入的网页有效 Calm 状态；bridge 校验主 frame、本机服务来源与合法模式值。

Quick Capture 的成功反馈来自真实保存完成；SQLite 成功之前不飞入、不显示已收藏。真实保存的飞入（900ms）结束后是（15）粒子与 ring；没有来源矩形时直接显示成功 burst。分类和通用主要控件点击有（6）粒子的动作提示，它不承载“已保存”语义；设为常用的（6）粒子仅在真实写入后触发。

详情临时代理（710ms）不接管焦点或点击，真实详情立即可用；内容分层进入，对话框本体（400ms）与文字 stagger 独立于业务流程。Bits 在 Studio 内执行（680ms）FLIP、（850ms）模糊入场与（500ms）退出代理，退出最多（9）个、只取可见卡片；切换和销毁时清理。Hover 的聚光与 sheen 不挪动控件命中区。保存失败与编辑冲突仍走原恢复路径。

## Do's and Don'ts

- Do 延续已经认可的 Creative Tech Dark · Motion Studio，按真实源码提取令牌。
- Do 使用真实封面、域名、资源名称、数量、附件和文本摘要。
- Do 让 Studio、Calm、系统减少动态效果与弹层生命周期控制装饰动效。
- Do 在写入成功后反馈收藏，失败保留输入与恢复动作。
- Do 保留可见焦点、键盘操作、清晰错误与原生系统结构。
- Don't 恢复旧的暖白／鼠尾草／整页玻璃视觉，或复活旧 Olla 装饰模块。
- Don't 用 Demo 的示例内容、localStorage 资源模型或模拟成功替代真实 API。
- Don't 给实际卡片叠加第二套 FLIP／tilt，或让代理元素阻挡内容操作。
- Don't 将网页预览截图作为 iPhone 原生实现或全平台验收证据。


## Resource cover art · desktop restoration

本轮依据用户的卡片还原要求覆盖原先双列／域名占位表达；首页 Hero、品牌动画、原生 iPhone 不变。详见 `../docs/shiji-v2/card-restoration/REPORT.md`。

真实 `coverId` 附件、`thumbnail` 和已有网站截图仍优先。仅无图或加载失败时显示派生排版封面，不写回资源。Tool 用 oat 底、大字、点阵和实际技术字段；Design 用 cyan 底、裁切环与标题；Motion 用 lime 底、斜体大字、透视线场和紫／珊瑚环；Code 用 blue 底、真实缩进／行号和本地词法着色；Prompt 用 coral 底、轻旋转标题、真实摘要与紫色星形；Article 用 yellow 底、大标题与编辑横线；Audio 用 violet 底和装饰信号线；其他 File 用暗底和折叠几何。装饰信号线不代表解析过音频。

新增封面材料：oat #f0ece3、yellow #ffd954、coral #f5b8a9、blue #171b36。封面墨色 #171b25；环墨色 #193950；Prompt 星形 #7543cb；文章星形 #b64d18；音频线色 #32234c。代码正文 #e8e9fb、行号 #9298ba、注释 #a3b1cd、字符串 lime、关键字 #c5b7ff、数字 #ffb8a4。颜色只属于封面内容，不改变产品状态语义。字体沿用认可的系统字族；代码采用系统等宽。

封面标题使用容器字号和有限行数，完整名称仍在卡片正文与详情标题可读。SVG 只做自绘几何，不借用其他品牌标志或外部作品。原先仅内部图形的 6px 指针反馈已由下述整卡姿态替代，继续复用 Bits 已有监听；无新增循环、FLIP 或 Tilt owner。Calm／系统减少动态禁用内部位移和过渡。详情代理复制真实图像或当前海报，期间暂时隐藏目标视觉，完成／取消后恢复，避免双影。

### Whole-card tactile follow-up

根据用户对整张卡片摇晃／拖动手感的反馈，`card-motion-surface` 包含封面、标题、来源、操作与选择控件。ShijiBits 复用原指针 owner：外层 article 仅管理稳定 ID／瀑布流／FLIP，内层 surface 管理整卡姿态；不在图片上再叠加 tilt。仅鼠标／精细指针、Motion Studio、画廊 frame 模式响应。静止卡片没有 transform 或 will-change。

鼠标轻晃上限 5°、抬升 8px；按压抬升 12px、缩放 1.025；封面拖动采用 tanh 阻力、位移上限 36px 和侧转上限 4°。超过 6px 后松手消耗本次点击，以免误开详情；小幅按压仍按既有详情流程处理。550ms 弹性回落可被下一次手势中断，不保存排序。滚动、焦点移出、Esc、重排、失去捕获、页面隐藏、Calm／系统减少动态及销毁清理姿态和捕获。列表／看板用 display:contents 保留原布局，触摸／笔仍使用原生点击与滚动。


## Cover Studio 2.0 · P0–P3

Cover Studio supersedes the fixed per-type poster treatment above, while preserving the complete Hero, three-column/featured masonry and whole-card tactile owner. Saved semantics select eight art families; an immutable ID (canonical URL fallback) independently selects one of three compositions and a coordinated palette. Mutable tags, favorite state, sorting and view dimensions do not pick a new variant/theme. User/local/actual website images keep precedence. The frozen old renderer is QA-only.

Nine cover-only palettes are cream/ink, acid lime/charcoal, electric violet/deep blue, signal cyan/navy, coral/burgundy, yellow/black, monochrome, chrome and dark navy. Titles use local system sans, Georgia / Songti SC for editorial serif, and ui-monospace / SFMono-Regular / Menlo for terminal and actual code. Typography bounds are 16–96px for titles, 10–15px source/caption/excerpt and 10–19px code/title; container width, native glyph measurement, word packing and per-composition height determine intermediate sizes. Negative tracking stays at −0.02 to −0.035em, title line-height 1.1. Actual saved code is syntax-colored with readable dark ink on light editor surfaces.

No new cover pointer/FLIP owner, continuous cover animation, runtime dependency, database field or stored cover preference was introduced in this phase. Calm and reduced-motion behavior remain under the existing controllers. Variants, actual screenshots, isolated QA reproduction, initial long-task result and pending P4–P9 are documented in `../docs/cover-studio-2/REPORT.md`.

## V3 Beta integration of V2.1

Preserve the art branch renderer, whole-card gesture, three-column/featured masonry and approved Lab references. V2.1's simpler five-cover CSS/renderer is not loaded in parallel. Native V2.1 real-field covers/safe-area rail and share-session guard remain native implementations. Bits continues to own card FLIP and gesture: reorder 480ms, entry 520ms, capped 175ms stagger, exit 240ms. Detail is 560ms with the original wide-poster identity and target hide/restore; modal entry 320ms / inert exit 160ms; search focus 220ms. Cancellation restores visible targets. Large Hero markup, dimensions and continuous brand loops remain unchanged. Only V2.1 control/recovery/modal styling is retained; see ../docs/shiji-v3-beta/REPORT.md for current evidence and limits.

### Approved photographic preview integration

The bundled Poly Haven homepage capture now uses the accepted Lab photographic print: forest #19392e, cream #f3f0d9 title, real category in lime, and a 7-degree paper frame. The existing 1280×720 source is cropped to x=820..1240, y=120..510 using CSS, removing navigation/logo/repeated site heading. Title/category/domain derive from the saved record. Only that known bundled snapshot gets this presentation; user attachments and arbitrary actual thumbnails remain unchanged. Both card and detail call the same preview renderer. Nested-image failure hides the whole print and exposes the generated fallback; keyed media reuse retains failure state. Poster-local container units preserve composition through the existing detail proxy. No new animation owner, resource fields or dependencies.
