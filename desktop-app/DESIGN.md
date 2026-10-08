---
name: "拾集 · 桌面 App 与浏览器采集助手"
description: "清晰的大图资源画廊，连接本机浏览器采集与整理。"
colors:
  bg: "#f7f7f2"
  sidebar: "#eeeee7"
  paper: "#fff"
  ink: "#243631"
  muted: "#596963"
  line: "#daddd4"
  accent: "#325a4a"
  accent-hover: "#234737"
  accent-soft: "#e1ebe2"
  glass-fill: "rgba(253,254,249,.86)"
  capture-fill: "rgba(250,253,248,.57)"
  native-capture-ink: "rgb(8% 13% 10%)"
  nav-active: "#dce8dc"
  secondary-fill: "#e8eee6"
  tag-fill: "#e7ece3"
  tag-active: "#d1e1d0"
  field-fill: "#f8faf4"
  field-stroke: "#aebbaa"
  focus-ring: "#52715a"
  selection: "#cddfce"
  opaque-material: "#f5f8ef"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "34px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-.025em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-.015em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "16px"
    lineHeight: 1.6
  control:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "14px"
    fontWeight: 600
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "13px"
    lineHeight: 1.5
  metadata:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"PingFang SC\", \"Noto Sans SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: "12px"
    lineHeight: 1.6
rounded:
  preview: "14px"
  navigation: "11px"
  field: "10px"
  toolbar: "22px"
  dialog: "24px"
  popup-control: "15px"
  pill: "999px"
spacing:
  small: "8px"
  control-gap: "12px"
  medium: "16px"
  section: "24px"
  workspace: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.paper}"
    typography: "{typography.control}"
    rounded: "{rounded.pill}"
    padding: "11px 18px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-secondary:
    backgroundColor: "{colors.secondary-fill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "10px 16px"
  search-field:
    textColor: "{colors.ink}"
    rounded: "{rounded.preview}"
    padding: "0 10px"
  navigation-active:
    backgroundColor: "{colors.nav-active}"
    textColor: "{colors.ink}"
    rounded: "{rounded.navigation}"
    padding: "9px 12px"
    height: "40px"
  category-active:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "7px 13px"
    height: "38px"
  tag:
    backgroundColor: "{colors.tag-fill}"
    textColor: "{colors.muted}"
    rounded: "{rounded.pill}"
    padding: "6px 12px"
  resource-metadata:
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    padding: "14px 2px 0"
  form-field:
    backgroundColor: "{colors.field-fill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
  browser-capture-deck:
    backgroundColor: "{colors.capture-fill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "6px"
  native-capture:
    textColor: "{colors.native-capture-ink}"
    rounded: "{rounded.pill}"
    padding: "14px 22px"
  extension-button:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.paper}"
    rounded: "{rounded.popup-control}"
    padding: "12px 14px"
---

# Design System: 拾集 · 桌面 App 与浏览器采集助手

## Overview

**Creative North Star: "清晰画廊上的采集层"**

拾集的视觉重心是实际收藏的大图、名称与来源。暖白纸面、深绿文字和低饱和鼠尾草绿让内容自己的颜色进入画廊；系统字体承担持续搜索与整理的工作，不制造另一个展示品牌。

玻璃用于操作层的浮起与上下文联系。macOS 原生采集浮层读取下方资源图像的颜色，标签和图标保持深色可读；浏览器使用明确的 CSS 材质近似。图片、正文和来源信息保持清晰。用户已否定割裂的 Olla 装饰循环与覆盖内容的大块白色磨砂面板。

**Key Characteristics:**
- 实际资源图像提供主要视觉变化
- 暖白纸面、鼠尾草绿操作、清晰深色文字
- 小型原生操作浮层与稳定的内容平面
- 动作触发的有限形变与可见键盘焦点

## Colors

规范值在 frontmatter；最终网页叠层来自 `static/liquid-glass.css`，它覆盖基础样式与旧资源动效样式。不要从较早的 Solarized 或 Recent Motion 声明重新提取主题。

### Primary

**鼠尾草深绿**（accent / accent-hover）用于主要操作、选中分类与链接；**浅鼠尾草**（accent-soft、nav-active、tag-active）为导航与标签的选中提示。普通分类与标签使用 muted，活动分类在深绿底上使用 paper。

### Neutral

**暖白纸面**（bg）承接画廊；paper 用于详情与表单。**深绿墨色**（ink）用于主体，**叶灰绿**（muted）用于域名、数量和提示，line 用于已有信息分隔。secondary-fill 和 tag-fill 是小型控件的浅色背景。

**透明暖白**（glass-fill / capture-fill）是浏览器的材质填色，不是原生材料令牌。**原生采集墨色**（native-capture-ink）精确保留 SwiftUI 的 RGB 比例；它与白色轻染的原生玻璃共同保障图像上方的文字对比。focus-ring、selection、field-stroke 与 opaque-material 分别用于焦点、选区、输入边界及不透明回退。

**The Content Color Rule.** 让实际资源图像提供颜色；界面配色服务于搜索、选择和编辑，不补造装饰性主题色。

## Typography

**Display / Body Font:** 系统与中文字体栈，规范值在 frontmatter。原生壳与配对面板使用 SwiftUI 系统字体；浏览器扩展也沿用系统字体。这是当前工具界面的排版选择，不宣称自有展示字体。

### Hierarchy

- **Display:** 工作区标题，常规宽屏使用 display；760px 以下降至30px，480px 以下28px。
- **Title:** 图片下资源名称使用 title；480px 以下为19px。标题保留自然换行，不通过缩小字体隐藏长名称。
- **Body:** 详情说明与编辑正文使用 body；来源和许可随真实内容显示。
- **Control / Label:** 主按钮与搜索为14px，快速分类为13px；480px 以下分类为12px。原生采集入口为14px semibold。
- **Metadata:** 域名、附件数量、分类与辅助说明使用 metadata；数量沿用 tabular-nums。扩展正文为14px/1.6，标题为21px/1.3、600字重，连接状态为11px。

## Layout

采用内容平面加操作层的空间关系。资源网格、名称、来源是连续的阅读区域；表单与详情承接选中的资源，面板具有真实的编辑或检查目的。

当前桌面画廊固定为两列最短列排列，480px 及以下一列；桌面列间距22px，760px 及以下18px。网页侧栏为226px；1170px 及以下改为可展开导航。常规工作区左右32px，1170px 以下24px，760px 以下20px，480px 以下16px，最大宽度1500px。底部保留110px滚动余量。默认预览框比例为1.6；完整显示使用真实已加载图像比例，已有96–560px高度约束与 contain 适应不改写原图元数据。

浏览工具是分类、筛选、显示和选择。760px 以下分类横向滚动，并与工具入口分行。移动端只让分类自身滚动，不让整个文档产生横向溢出。列表与按形式分组的参考板继续使用各自布局，不套用灵感板的列数。

原生与浏览器的首屏构图、浮层位置和验证尺度记录在 `.impeccable/surfaces/desktop-app.md`，不是其他未来页面必须复制的模板。

## Elevation & Depth

内容卡片平置，无独立背景、边框或悬停投影。浏览器顶栏与分类操作区使用轻透明暖白和柔软、有偏移的投影；详情与编辑面板以更明确的层级承接工作。原生玻璃由 macOS 渲染，不能由 CSS 阴影参数替代。

### Shadow Vocabulary

- **操作层低浮起:** `0 8px 28px rgba(30,48,36,.09)`，浏览器顶栏。
- **小控件浮起:** `0 3px 14px rgba(30,48,36,.06)`，分类与浏览工具。
- **工具面板:** `0 12px 40px rgba(30,48,36,.17)`，筛选等面板。
- **详情抽屉:** `-14px 0 50px rgba(30,48,36,.15)`。
- **对话框:** `0 16px 50px rgba(30,48,36,.2)`。
- **浏览器采集层:** 两条中性内侧光缘与 `0 6px 22px rgba(26,44,34,.16)`，背景模糊12px、饱和度1.5。光缘是透明材质边界，不为卡片增加装饰性双重轮廓。

**The Clear Content Rule.** 玻璃属于操作层；资源预览与正文不附加磨砂、光晕或图像倾斜。

**The Deliberate Motion Rule.** 形变回应明确操作或布局变化；不恢复自动循环的装饰舞台。

原生展开使用有界 spring（response 0.38、dampingFraction 0.82），稳定 glassEffectID 在同一 namespace 内关联动作。分类指示器只在选择或布局改变时运行320ms、cubic-bezier(.16,1,.3,1)。继承的画廊重排为有限320ms，首次进入从已可见状态作有限360ms位移，不形成新装饰循环；最终叠层禁用图片倾斜和 CSS 卡片入场。Reduce Motion 关闭原生 spring 与相应网页空间动画；浏览器减少透明度或不支持 backdrop-filter 时使用 opaque-material。macOS 14/15 使用系统 regularMaterial 回退，macOS 26 使用原生材料及系统辅助功能处理。

## Shapes

大图使用柔和圆角（preview），不将整张资源包进带阴影的圆角卡片。navigation 与 field 比浮层更克制；toolbar、dialog 给工具面板足够舒适的转角。胶囊仅用于小型按钮、分类、标签和采集控件；原生关闭与扩展入口为圆形。扩展按钮保持 popup-control 的轻圆角，不将整页所有表面改成胶囊。

## Components

### Buttons

主要按钮为深绿填色、白字、胶囊与清晰动作名；悬停使用 accent-hover。次要按钮用 secondary-fill 和 ink，悬停浅绿。详情页“编辑”为唯一主要动作，来源、常用、加入项目与加标签保持次级。等待和禁用状态不得伪装成已完成；键盘焦点使用可见两像素轮廓。

### Chips

标签和可移除筛选条件保持小而稳定。普通标签为 tag-fill / muted，活动标签为 tag-active / ink。准确名称按完整字符串显示，逗号不作为视觉分隔符。选中与可移除状态不能只通过动画表达。

### Cards / Containers

资源以真实预览图、标题、域名、附件数量、分类和预览动作组成；图片下信息内边距14px 2px 0。封面区域和标题均可进入详情，常用控件有单独的操作名称和状态。完整预览保持原图，不给图片额外倾斜或悬停放大。侧车中的资源组件只展示可复用的信息原语，不放整页截图或虚构图片。

### Inputs / Fields

搜索是透明、无边框的小型输入；聚焦时整体底线与浅绿表面提示位置，输入文字区域不另加矩形描边。编辑字段为 field-fill、field-stroke 与 field 圆角；聚焦轮廓与错误文本清晰可见。扩展字段保留白底、9px圆角与相同主题焦点。

### Navigation

侧栏选中项为 nav-active 与加重的 ink。快速分类使用固定文字、真实库数量和胶囊点击区，选中深绿底配白字；指示器不改变按钮的可点击尺寸。窄屏导航可关闭，Esc 与焦点返回沿用已有行为。不要恢复被隐藏的 Dock 放大图标作为当前设计系统。

### Capture Layer

macOS 26 的采集入口使用 `GlassEffectContainer`、交互式 `glassEffect` 与稳定 `glassEffectID`，白色 tint opacity 0.65、native-capture-ink 前景。按“收藏”展开为真正的“收藏网址 / 添加素材”，选择动作收起；扩展入口打开原生配对面板。详情、编辑和对话框打开时浮层隐藏。浏览器的两个采集动作固定显示，以 CSS 模糊和中性光缘近似；侧车仅预览这份浏览器原语，不能预览或证明 SwiftUI 材质。

### Pairing / Extension

配对面板使用系统标题、分组、真实本地地址、文件夹动作和复制按钮。加载、失败与重试分别显示；仅有效配对码才启用复制。扩展为360px宽、24px内边距的简洁动作面板，连接状态有文字，失败提示可恢复。不要将配置值画成产品装饰。

## Do's and Don'ts

### Do:
- Do 使用实际封面、准确名称、真实数量和来源信息。
- Do 在深色和浅色图像上检查浮层标签与图标的可读性。
- Do 让控件保留可见焦点、明确动作名及加载、失败、禁用反馈。
- Do 保留原生材质、减少动态效果与不透明回退的区别。

### Don't:
- Don’t 把 CSS backdrop-filter 称为原生 Liquid Glass。
- Don’t 恢复 Olla 循环装饰或在资源图像上叠加磨砂面板。
- Don’t 通过截图、示例封面或颜色推断资源的价格与许可。
- Don’t 将整个界面截图当作组件，或用外部图标依赖代替可独立渲染的图标。
