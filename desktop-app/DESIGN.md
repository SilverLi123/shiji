---
name: "拾集 SHIJI V5 · Spatial Poster"
description: "深色空间画廊：荧光绿操作、紫色几何舞台与真实收藏海报。"
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
  shiji-violet: "#a58cff"
  shiji-cyan: "#79dfff"
  brand-wash: "#d5b5ff"
  brand-gradient-start: "#a991f6"
  brand-gradient-end: "#8b6ae0"
  control-muted: "#b5b7bf"
  control-hover: "#292d34"
  field-stroke: "#424650"
  poster-ink: "#15171d"
  poster-paper: "#e8e7df"
  poster-cream: "#eeede4"
  poster-acid: "#daff67"
  poster-gold: "#fbd151"
  poster-rose: "#f0aeaa"
  poster-turquoise: "#87e5ef"
  poster-lavender: "#c9b7ff"
  poster-coral: "#f48772"
  terminal-surface: "#151d1c"
  terminal-ink: "#d4ead5"
  error-fill: "#332321"
  error-ink: "#ffb2aa"
  error-stroke: "#734a45"
  pending-license-fill: "#433918"
  pending-license-ink: "#ffe395"
typography:
  display:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "clamp(42px,5.3vw,79px)"
    fontWeight: 850
    lineHeight: 1.12
    letterSpacing: "-.059em"
  headline:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-1.4px"
  section-title:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "25px"
    fontWeight: 850
    lineHeight: 1.2
    letterSpacing: "-.036em"
  poster-title:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "var(--poster-title-size,18cqw)"
    fontWeight: 900
    lineHeight: 0.97
    letterSpacing: "-.065em"
  brand-display:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "clamp(35px,4vw,59px)"
    fontWeight: 1000
    lineHeight: 0.9
    letterSpacing: "-3.4px"
  title:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 800
    lineHeight: 1.3
    letterSpacing: "-.6px"
  body:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "16px"
    lineHeight: 1.6
  description:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "13px"
    lineHeight: 1.85
  control:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "12px"
  navigation:
    fontFamily: "Inter, \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 620
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "clamp(10px,3cqw,14px)"
    lineHeight: 1.65
rounded:
  tag: "6px"
  control: "8px"
  mode: "9px"
  navigation: "11px"
  preview: "12px"
  detail-preview: "13px"
  stage: "16px"
  spatial-pane: "20px"
  spatial-scene: "22px"
  hero-pill: "30px"
  category-pill: "999px"
spacing:
  tag-gap: "7px"
  small: "8px"
  control-gap: "12px"
  medium: "16px"
  gallery-column-gap: "18px"
  panel: "20px"
  section-gap: "24px"
  hero-gap: "30px"
  gallery-row-gap: "33px"
  hero-block: "39px"
  workspace-inline: "clamp(22px,4vw,64px)"
components:
  button-primary:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "#15161a"
    rounded: "{rounded.navigation}"
    padding: "11px 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-hero:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "#141515"
    rounded: "{rounded.hero-pill}"
    padding: "13px 17px"
  button-secondary:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  search-field:
    backgroundColor: "{colors.shiji-surface}"
    textColor: "{colors.shiji-fg}"
    typography: "{typography.control}"
    rounded: "{rounded.preview}"
    padding: "0 12px"
    height: "38px"
    width: "260px"
  navigation-active:
    backgroundColor: "#25272a"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.navigation}"
    padding: "11px 12px"
  category-active:
    backgroundColor: "{colors.shiji-lime}"
    textColor: "#15171a"
    rounded: "{rounded.category-pill}"
    padding: "10px 14px"
  category-default:
    backgroundColor: "#16181d"
    textColor: "{colors.control-muted}"
    rounded: "{rounded.category-pill}"
    padding: "10px 14px"
  poster-card:
    rounded: "{rounded.preview}"
    height: "230px"
  poster-card-wide:
    rounded: "{rounded.preview}"
    height: "300px"
  form-field:
    backgroundColor: "{colors.shiji-surface-raised}"
    textColor: "{colors.shiji-fg}"
    rounded: "{rounded.control}"
    padding: "12px"
  spatial-pane:
    rounded: "{rounded.spatial-pane}"
    width: "min(31vw,270px)"
    height: "190px"
---

# Design System: 拾集 SHIJI V5 · Spatial Poster

## Overview

**Creative North Star: "Spatial Poster · Creative Archive"**

拾集把真实收藏置于深色空间画廊：荧光绿连接操作与选择，紫色品牌舞台以网格、裁切几何、半透明平面和漂浮层次表达创意。海报本身成为浏览表面；管理信息在列表和详情中保持清楚。

当前世界由用户提供的 SHIJI_V5_Spatial_Poster_Demo.html 明确授权，原稿保存在 ../docs/shiji-v5/reference/spatial-poster.html，方向契约见 ../docs/shiji-v5/PLAN.md。规范以实际最后加载的 static/shiji-v5.css、static/shiji-v5.js、index.html 与保留的基础控件为准；本次合并替换 V2 世界和旧 Cover Studio 附录，保留已经确认的数据与原生平台边界。范围是 macOS WKWebView／响应式网页，原生 iPhone SwiftUI 未改变。

**Key Characteristics:**

- 深色空间底、荧光绿动作、紫色层叠品牌舞台
- 海报、网格、颗粒和几何实体共同构成内容材质
- 图库和空间卡只展示封面，列表与详情承载管理信息
- Studio／Calm、3D／Flat 与系统减少动态效果共同控制深度
- 真实图片优先，海报从真实记录派生，原生操作保持平台材料

## Colors

frontmatter 是规范值。界面强调色与海报材料分开使用：深色控件保持稳定，封面可以使用多种明亮底色、渐变与印刷式叠色。

### Primary

**荧光绿**（shiji-lime）用于主要收藏操作、选中分类、焦点、常用状态、品牌图形与动作带；accent-hover 是基础主要按钮的悬停亮色。

### Secondary

**创意紫**（shiji-violet）用于品牌和空间材料。品牌舞台采用 brand-gradient-start／brand-gradient-end 渐变以及 brand-wash 的光晕；它们描述当前 V5 舞台，不沿用旧版渐变终点。

### Tertiary

**空间青**（shiji-cyan）用于空间模式、场景轨迹、几何和光晕。**海报材料色**（poster-paper、poster-cream、poster-acid、poster-gold、poster-rose、poster-turquoise、poster-lavender、poster-coral）属于不同资源构图；terminal-surface／terminal-ink 组成真实代码与仓库技术信息的终端平面。这些颜色不增加业务状态。

### Neutral

**画廊黑、侧栏黑、操作平面、抬升平面**（shiji-bg、shiji-sidebar、shiji-surface、shiji-surface-raised）由亮度差划分背景、导航和工作层。shiji-fg 是主要文字，shiji-muted 是基础辅助文字，control-muted 是控件次级文字，shiji-line 是精细边界。field-stroke 提供表单边界，control-hover 是次要操作悬停。poster-ink 是基础海报墨色；各构图允许在自身底色上采用实际深墨或浅字。

错误使用 error-fill／error-ink／error-stroke，待确认许可使用 pending-license-fill／pending-license-ink；都保留状态文字。高对比度偏好提升辅助文字和导航标签，详见 sidecar。

**The Content Color Rule.** 海报颜色属于内容表达；常用、选择、焦点与主要操作仍使用荧光绿，错误与许可状态仍有明确文字。

## Typography

**Display / Body Font:** frontmatter 中的 Inter／SF Pro Display 与本地中英文字体栈；没有外部字体加载。该字族来自用户指定 Demo，是本次视觉授权的一部分。

**Code Font:** 系统等宽字族，见 frontmatter。品牌标题紧凑而有力度，海报标题紧贴几何构图；管理正文、表单和详情沿用中性阅读秩序。紫色句点使用 Georgia 衬线斜体作为局部品牌符号，不据此扩展一套衬线正文。

### Hierarchy

- **Display:** 两行品牌主标题；中宽桌面分支为 `clamp(38px,4.6vw,60px)`，窄工作区为 `clamp(38px,5.4vw,62px)`，手机网页为 `clamp(43px,10vw,64px)`、行高（1.1）与字距（-.06em）。
- **Headline:** 空间说明标题；在（1180px）及以下改为（26px），手机网页为（24px）。
- **Section Title:** 资源库标题；手机网页为（23px）。
- **Poster Title:** 从名称字形宽度计算（6.8–25cqw），最多四行；Linear 构图有（16cqw）上限，空间／详情有自身上限。Prompt 真实摘要为 `clamp(10px,3.2cqw,15px)`、行高（1.5）。
- **Brand Display:** 品牌舞台中的 KEEP IDEAS. 图形文字；手机网页为（46px）。
- **Title:** 列表资源标题；封面外标题不出现在纯封面图库。完整名称在可访问名称和详情中保留。
- **Body / Description:** 基础正文与 Hero 说明；空间说明为（13px／1.7），列表介绍为（12px／1.6）。
- **Control / Navigation:** 搜索、分类和主要操作采用紧凑字号；motion、replay、小动作入口最终为（11px）。
- **Code:** 海报终端展示真实代码，保留缩进；详情的代码阅读层沿用（13px／1.8）。

**The Container Type Rule.** 海报标题随封面容器和真实名称计算字号；不以视口字号覆盖派生标题，也不补造短标题。

## Layout

桌面固定侧栏宽（238px），顶部栏高（74px），工作区最大宽（1770px），水平留白使用 frontmatter 的 workspace-inline；底部留白（120px）。Hero 默认左右两栏，品牌舞台占（39%）且至少（290px），间距与垂直留白见 spacing；空间展台采用（280px + 剩余宽度）两栏，场景高（290px）。空间卡从当前匹配资源取最多三条，不足时不复制填充；回收站与库检查不展示该展台。

图库由 ShijiBits 计算瀑布流：大于（900px）三列，（621–900px）两列，（620px）及以下一列，水平间隔和纵向间隔分别使用 gallery-column-gap／gallery-row-gap。三列、舒适密度、构图预览下，具有真实非空技术字段的 Tool 资源可以跨两列；紧凑密度、完整图片和窄屏不跨列。基础封面高（230px），宽卡（300px），紧凑封面（190px）；手机网页的普通／宽卡均为（230px），完整图片模式采用真实图片比例。稳定 ID、首次 60 条与每次追加 60 条保留。

响应式以不同职责分支，而不是一个通用断点：

- （1380px）及以下桌面工具栏压缩，搜索宽（190px）；（1120px）及以下桌面工作区水平留白（32px）、搜索（170px）、Hero 减小，空间说明列（230px）。
- （1180px）及以下空间场景高（250px）；（881–1120px）空间卡（210×160px）。
- （880px）及以下侧栏收为（260px）抽屉，主工作区无侧栏偏移，顶部栏高（65px），工作区水平留白（24px），空间说明／场景上下排列，场景高（240px）。网页固定底部导航出现；macOS 原生宿主隐藏该网页底栏。
- （620px）及以下工作区水平留白（16px）、底部留白（110px），Hero 上下排列，品牌舞台高（250px），空间场景高（215px）、卡片（168×130px）。搜索收为图标，获得焦点后横向展开；工具栏收藏由其他既有收藏入口承接，筛选、显示、选择仍可访问。
- （480px）及以下仍保留基础详情与控件触控适配；（430px）是 Demo 的极窄工具栏／艺术层校准，不改变图库的单列阈值。

## Elevation & Depth

V5 的空间深度是世界的一部分：暗色平面与网格底场承接透视卡片，紫色舞台叠放实体、环线和 CSS 半透明材料。海报内部允许印刷式偏移影、颗粒、渐变、裁切和层叠几何；不能把这些用户指定材料当作全局禁用项。图库外壳不增加另一层面板，预览与空间卡承担阴影和材质。

### Shadow Vocabulary

- **图库静态预览:** `0 5px 18px #0003`。
- **空间模式悬停预览:** `0 28px 70px #000b,0 0 0 1px #c9e0ff38 inset`。
- **空间品牌舞台:** `0 26px 65px #0009,0 0 0 1px #ffffff12 inset`。
- **空间卡片外壳:** `0 22px 48px rgba(0,0,0,.58),inset 0 0 0 1px rgba(255,255,255,.06)`。
- **工具面板:** `0 16px 40px #0006`。
- **详情抽屉:** `-16px 0 50px #0008`。
- **对话框:** `0 24px 80px #0009`。
- **网页采集层:** `0 8px 32px #0006`；Toast 为 `0 10px 30px #0006`。

**The Single Motion Owner Rule.** ShijiBits 独占资源卡 FLIP、整卡指针姿态与拖动；ShijiMotion 负责品牌／空间舞台、有限反馈和暂停，不对同一个实际卡片节点叠加第二套 transform。

**The Material Boundary Rule.** 网页透明平面和 backdrop-filter 是 CSS 材质；macOS 原生操作使用系统材料，不把网页效果称为原生 Liquid Glass。

Studio／Calm 保存在网页偏好，3D／Flat 是独立展示偏好；系统 `prefers-reduced-motion` 优先。Flat 去掉动态透视，Calm 与系统减少动态效果停止动态深度。品牌与空间循环在后台、不可见或详情／对话框打开时暂停，海报循环只在 Studio 且海报可见时运行。减少透明度沿用实色操作平面；装饰结束不是内容可用的前提。具体 easing、动画时长和焦点扩展在 sidecar。

## Shapes

紧凑控件、搜索和海报预览使用不同圆角层级，见 frontmatter；分类与 Hero 操作采用胶囊，空间卡和场景使用更宽的圆角。品牌标记是荧光绿圆角块中的自绘折线与角部圆形裁切；舞台书签由 Demo 的 SVG 几何构成。卡片构图允许裁切圆环、球体、扭转块、终端平面与胶印式错位，边界仍裁切在预览内部。

详情为直角右侧阅读平面，宽 `min(500px,100vw)`；手机网页全宽。对话框沿用（16px）圆角。图标采用现有 SVG 文件或内联 SVG；艺术里的几何符号属于构图材料，不是新的导航图标语言。

## Components

### Buttons

主要操作明确、紧凑：工具栏主按钮采用 button-primary，Hero 使用 button-hero，次要任务沿用 button-secondary。基础按钮悬停变为 accent-hover，Hero 与工具栏按钮还有轻抬升与绿色光晕；文本操作悬停为荧光绿。键盘焦点是绿色（2px）轮廓，常规可聚焦按钮／输入偏移（4px）；真实 disabled 状态保留不可用语义与（.55）不透明度。

### Inputs / Fields

搜索为暗底圆角字段，焦点改为荧光绿边界；窄屏焦点横向展开并保留 Esc 返回焦点。表单为抬升平面、field-stroke 边界和 form-field 内边距。Quick Capture 网址输入仍采用（16px）文字、（15px）内边距，错误以深珊瑚背景和可恢复说明显示，失败保留草稿。

### Chips

分类是有真实数量的横向胶囊，默认暗底、细边界，选中为荧光绿底深字；小标签是（6px）圆角。列表、详情与筛选仍保留准确标签名称，包括逗号。不要从封面的小型艺术标签推导新的管理文案层级。

### Cards / Containers

**纯封面图库:** 非列表图库的封面外正文和 footer 隐藏，空间卡的元数据叠层隐藏；海报内部标题、来源、类别、标签和真实摘要仍属于封面。点击打开现有详情，可访问名称包含完整真实标题；选择模式的 checkbox 留在封面外独立层，仍可操作。列表继续显示行内资源标题、来源、标签与操作；手机列表缩减介绍和部分艺术层以保留阅读空间。

**真实图片与派生海报:** 用户 coverId、thumbnail、已有网页预览保持优先级，加载失败回到真实字段生成的海报。当前渲染器依据类型、域名、类别和名称／描述选择 Components、Motion、Spline、AI、Linear、Prompt、Retro、GitHub、Kinetic、Atlas、Code、Article 构图；不沿用历史 Cover Studio 的固定 ID 三变体规则。仓库终端只在真实 language／标签存在时出现，代码与提示词只展示保存的片段／摘要。封面生成不写回资源，Poster／Classic 是当前浏览器显示偏好。

**整卡手感:** 外层稳定 ID 与布局由 Bits 管理，内层 motion surface 管理姿态。仅精细指针与允许动效的图库 frame 模式响应；拖动超过（6px）消耗本次点击，避免误开详情，回落不保存排序。触摸／笔保留原生滚动和点击。滚动、Esc、失焦、重排、后台、偏好切换与销毁清理姿态和捕获。

### Navigation

侧栏当前项是暗色抬升块、主要白字、绿色图标与左侧绿色内边线；最小高度（43px）。hover 轻向右移动（3px）并提高对比。窄屏侧栏为可关闭抽屉；固定网页底栏的动作文字（11px）、触控高度至少（44px），中间收藏按钮为荧光绿。原生宿主使用既有平台操作入口。

### Spatial Deck / Brand Stage

空间卡和图库复用同一真实预览，最多三条真实匹配记录，并通过相同详情动作打开资源；静态布局根据一／二／三条记录调整，不造重复卡片。品牌舞台的几何材质来自用户 Demo；ShijiMotion 统一负责舞台指针、空间场景与暂停。装饰节点不接管点击或焦点。

### Capture / Detail

详情立即可用，有限视觉代理复制当前真实图片或海报，并在完成／取消后恢复预览，避免双影。成功飞入和粒子来自真实保存完成，失败继续走原错误／草稿恢复路径；一般控件粒子不表达“已保存”。

macOS 原生采集胶囊沿用系统半粗（14pt）文字、（46×46pt）图标按钮、（12pt）内部间距与 `GlassEffectContainer(spacing:16)`；macOS 26 使用真实 `.glassEffect(.regular.interactive())`，较早系统使用 `.regularMaterial`。网页采集层是实色暗底。原生展开遵守系统 Reduce Motion 与有效网页 Calm 状态，bridge 保留来源／主 frame 校验；本文件不改写原生 iPhone 设计系统。

## Do's and Don'ts

### Do:

- Do 以用户批准的 V5 Spatial Poster 和最后加载的源码作为当前视觉权威。
- Do 保留真实封面优先级、资源名称、来源、准确标签和实际代码／提示词内容。
- Do 让图库和空间卡保持纯封面；保留详情入口、完整 aria-label 与选择控件，列表继续展示行内信息。
- Do 让 Studio、Calm、Flat、系统减少动态效果与弹层／后台生命周期控制动效。
- Do 在真实写入完成后显示保存反馈，失败保留草稿、错误说明和恢复动作。
- Do 保留键盘焦点、稳定资源 ID、可追加浏览和原生平台边界。

### Don't:

- Don't 把历史 V2 字号、断点、Cover Studio 配色或变体规则重新当作当前海报规范。
- Don't 用 Demo 示例、模拟持久化、虚构来源或技术字段替代真实资源。
- Don't 给实际资源卡叠加第二套 FLIP／tilt，或让装饰代理阻挡点击和焦点。
- Don't 隐藏海报内的文字来实现纯封面；移除的是封面外管理正文与空间元数据层。
- Don't 让封面颜色构成价格、许可、AI 分析或音频解析的证据。
- Don't 将响应式网页截图作为原生 iPhone 实现或全平台验收证据。
