---
name: "拾集 SHIJI V2 · Native iPhone"
description: "Creative Tech Dark 品牌下的原生 iPhone 收藏画廊，保留系统导航与动态字体。"
colors:
  background-dark: "#0c0d10"
  background-light: "#f7f7f2"
  surface-dark: "#15171d"
  surface-light: "#ffffff"
  raised-dark: "#1d2027"
  raised-light: "#ededf0"
  secondary-text-dark: "#9d9eaa"
  secondary-text-light: "#555661"
  on-accent-dark: "#0c0d10"
  on-accent-light: "#ffffff"
  accent-dark: "color(srgb 0.843137 1.000000 0.396078)"
  accent-light: "color(srgb 0.313725 0.376471 0.117647)"
  brand-lime: "#d7ff65"
  brand-violet: "#a58cff"
  intro-symbol: "#835cf4"
  feedback-cyan: "#79dfff"
  feedback-coral: "#ff9d87"
typography:
  display:
    fontFamily: "-apple-system"
    fontWeight: 900
    letterSpacing: "-1pt"
  intro:
    fontFamily: "-apple-system"
    fontSize: "85pt"
    fontWeight: 900
    letterSpacing: "-3pt"
  title:
    fontFamily: "-apple-system"
    fontWeight: 600
  headline:
    fontFamily: "-apple-system"
  body:
    fontFamily: "-apple-system"
  label:
    fontFamily: "-apple-system"
    fontWeight: 600
    letterSpacing: "1pt"
  snippet:
    fontFamily: "ui-monospace"
rounded:
  preview: "14pt"
  brand-stage: "16pt"
spacing:
  small: "8pt"
  control-gap: "10pt"
  metadata: "12pt"
  gallery-inline: "20pt"
  text-preview: "22pt"
  detail-section: "24pt"
  gallery-card-gap: "28pt"
components: {}
---

# Design System: 拾集 SHIJI V2 · Native iPhone

## Overview

**Creative North Star: "Creative Tech Dark · Motion Studio"**

iPhone 延续已认可的 SHIJI V2 深色画廊、紫色品牌舞台与荧光绿收藏语言，同时把浏览、层级、搜索和编辑交给原生系统结构。真实大图、工具来源和可读文本摘要构成收藏的视觉主体。

原生默认使用 Creative Tech 深色外观，管理页可选择浅色或跟随系统。品牌通过 tint、显示排版、几何和有限动作表达；导航、TabView、Form、系统菜单、文件选取与 QuickLook 继续遵守 iPhone 使用习惯。它是独立 SwiftUI 应用，不能把网页手机预览当成源码或验收结果。

**Key Characteristics:**
- 深色优先、浅色与跟随系统可选的语义配色
- NavigationStack、三项 TabView 与系统搜索
- 动态字体、单列大图、较紧凑的无封面卡片
- 紫色品牌几何与少量荧光绿关键状态
- 原生收藏材料、可恢复保存与受控过渡

## Colors

frontmatter 的浅／深色值来自 `Shared/iOSImage.swift` 的 `NativePalette`。AccentColor 精确保留 Asset Catalog 的 sRGB 小数，而不是另造近似十六进制规范；brand-lime 与 brand-violet 来自 `NativeBrandHero` 的真实 RGB 比例。

### Primary

**交互荧光绿**（accent-dark）用于深色下的 tint、分类选择、常用标志与保存反馈；浅色使用较深的 accent-light，白色 on-accent-light 承接选中内容。原生 tint 读取 `Color("AccentColor")`，不得在普通控件中硬编码深色专用绿。

### Secondary

**创意紫**（brand-violet）与 **几何荧光绿**（brand-lime）属于 Hero 装饰，保持同一品牌形象。intro-symbol 用于开场的紫色符号，feedback-cyan／feedback-coral 与绿／紫共同组成短暂 burst。Text 预览目前使用系统 `Color.purple`，不是网页 text-preview-ink 的复制。

### Neutral

background、surface、raised 与 secondary-text 成对适配系统外观。主体文字使用 SwiftUI `.primary`，不能用固定白字替换。表单／列表继续使用系统语义背景、分隔与提示颜色；授权待确认沿用系统黄的透明填色，并同时显示文字。

**The Semantic Tint Rule.** 普通交互用自适应 AccentColor 与系统语义文字；固定品牌色只进入明确的展示几何。

## Typography

**Display / Body Font:** San Francisco，由 SwiftUI `.system` 和原生文本样式提供；中文由系统字体回退。**Snippet Font:** 系统 `.body` 的 monospaced 设计。

日常 UI 的 frontmatter 不声明固定原生字号；`.largeTitle`、`.title2`、`.title3`、`.headline`、`.subheadline`、`.caption` 与 `.caption2` 是实际 Dynamic Type 规格，映射记录在 sidecar。Hero 使用 `.largeTitle.weight(.black)` 与字距（-1pt）；卡片标题为 `.title3.weight(.semibold)`；详情标题为 `.title2.weight(.semibold)`；类型标签为 `.caption2.weight(.semibold)` 与字距（1pt）。来源／附件为 `.caption`，卡片说明与分类为 `.subheadline`。

辅助字号随系统文本样式变化，不把网页的微型英文工作台标签移植成固定点数。资源名可换行；来源与分类用 `ViewThatFits` 从横排降为纵排。无障碍字号时隐藏装饰 Hero，并使用更简单的空状态与收藏菜单。开场 `intro` 是一次性的品牌字标，源码使用固定展示字号，不能推广为正文或操作控件字号。

## Layout

根结构是三个各自包含 NavigationStack 的 Tab：资源库、集合、管理。图库使用 ScrollView 与 LazyVStack，水平内边距（20pt），顶部（10pt），底部（24pt）；卡片间距（28pt），卡内间距（12pt）。分类横向滚动，间距（8pt），每项左右内边距（16pt），最小高度（44pt）。

真实图片封面高（220pt），无可用图片的类型预览高（142pt）；详情封面高（240pt）。图库是单列原生布局，没有网页 CSS breakpoints。Hero 品牌舞台高（190pt），并通过字号条件退让给内容。详情分区间距（24pt），整体内边距（20pt）。

收藏层通过 `safeAreaInset` 放在底部右侧，保留系统 TabView 和安全区。正常字号使用横向可容纳的系统玻璃胶囊，`ViewThatFits` 在空间不足时退回菜单；无障碍字号直接使用菜单。系统搜索承接键盘，详情使用原生返回与边缘滑回。

## Elevation & Depth

图库默认是清晰的内容平面，卡片没有额外手工阴影或磨砂蒙版。iOS 26 的收藏控件使用 `.glassEffect(.regular.interactive())` 与 `GlassEffectContainer`；较早系统及布局回退使用 `.regularMaterial` Capsule 菜单。底部编辑操作使用系统 `.bar` 背景。材质不是资源图像的滤镜，不使用 CSS 玻璃模拟。

**The Platform Structure Rule.** 品牌进入 tint、内容和展示动作，导航、搜索、表单、系统模态与材料继续由原生组件承担。

`shiji-v2-motion-mode` 保存 Studio／Calm；`accessibilityReduceMotion` 优先。原生以 `NativeMotionIntro` 实现（1370ms）品牌幕布，SceneStorage 控制首次展示，Hero 提供重播；跳过、Calm、系统减少动态或离开 active scene 会结束开场。Hero 用 TimelineView 请求最小（1/30s）更新时间，驱动书签、虚线轨道、tracer、cutout 和 spark；Calm、非 active scene、不可见时暂停。此为调度规格，不代表实测帧率。

`NativeMotionReveal` 使用（850ms）有限模糊／位移进入，详情文字有分层延迟；分类／范围变化使用短暂 stamp 与（6）粒子，网址写入成功后同时出现原生（900ms）飞入、（15）粒子和文字提示。常用状态真实写入成功后才显示（6）粒子。系统 zoom 与 spring 保留平台过渡；详细参数与系统可用性见 sidecar。

## Shapes

预览采用 RoundedRectangle（14pt），Hero 舞台采用 RoundedRectangle（16pt）；分类、保存反馈和收藏控件使用系统 Capsule／Circle。书签几何的缺口在高度（72%）处，装饰与真实资源缩略图分开。表单、分组列表与系统 Alert 使用平台轮廓，不添加网页式全局自定义容器。

## Components

本文件的 frontmatter `components` 与 sidecar `components` 留空：应用没有可直接注入 Shadow DOM 的 HTML 组件。真实 SwiftUI 规格在下列条目及 sidecar `extensions.nativeComponents`；不以 HTML 示意伪装实际原生运行时。

### Navigation / Search

TabView 只承载“资源库／集合／管理”三项页面；收藏动作留在独立收藏层。图库显示系统大标题和 `.searchable`；深层详情切换 inline 标题。工具栏保留电脑同步与浏览范围菜单；SF Symbols 承担原生图标。

### Cards / Covers

Visual 使用实际本地封面；Tool 来自 `kind=website` 且分类“开发工具”；Text 来自 `kind=code/prompt`。呈现类型是派生值，不序列化到 schema 3。缺图显示系统符号和真实域名／类别；Text 有摘要时最多显示实际内容的前（240）字符。卡片合并为 VoiceOver 可读组，纯封面装饰从可访问性树隐藏。图库卡片通过 NativeMotionReveal 入场，并在分类 spring 的上下文中采用非对称插入／移除过渡；系统减少动态或 Calm 省略这类动画。

### Capture Dock

iOS 26 使用 `GlassEffectContainer(spacing:14)`，内部间距（10pt）。网址与素材按钮左右内边距（18pt）、最小高度（48pt）；收起图标（48×48pt）；默认收藏按钮左右（20pt）且最小高度（48pt）。系统菜单回退保持相同两项动作，文件选取使用系统 fileImporter。

### Editor / Persistence Feedback

编辑使用原生 Form，导航栏明确“取消／保存”；未保存草稿阻止滑动误关闭并提供放弃确认。真实 `files.save` 成功、重新载入后才递增 captureSequence、关闭编辑并触发“已收藏到拾集”与 VoiceOver announcement。保存错误保持编辑页及输入，不能在点击时提前播放成功反馈。当前新增文件路径会刷新库，但不递增同一 URL 保存反馈计数；不要声称所有采集方式已有同一成功动画。

### Detail / Management

详情保留来源、授权、备注、标签和附件；编辑是底部主要操作。管理、集合和回收站使用原生 List／Form／Picker，备份确认与冲突选择继续采用可读文字和系统模态。同步、备份与分享能力的事实以 PRODUCT.md 为准；分享扩展空白页没有因视觉升级而修复。

## Do's and Don'ts

- Do 延续 Creative Tech Dark 品牌，并保留浅色／跟随系统的语义配色。
- Do 使用 Dynamic Type、SF Symbols、原生导航、系统搜索与系统任务模态。
- Do 保留至少 44pt 的主要触控规格，并在空间和字号变化时退回可用布局。
- Do 在真实本地保存成功后显示反馈，失败保留编辑与恢复路径。
- Do 在 Studio 与系统减少动态效果之间始终让系统偏好优先。
- Don't 把网页 CSS、HTML 片段或手机浏览器截图宣称为原生组件与原生验收。
- Don't 用固定白字／深色专用绿替代自适应文字与 AccentColor。
- Don't 让原生品牌循环绕过 Calm、系统减少动态、scene 与可见性条件，或引入 hover 专用交互和第二套导航模型。
- Don't 宣称分享扩展、旧系统回退或全部 iPhone 机型已通过本轮验证。
