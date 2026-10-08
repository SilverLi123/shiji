# Codex 执行指令 — 拾集 SHIJI V2 Motion Studio

你是负责 **SwiftUI / WKWebView / HTML-CSS-JavaScript / Python SQLite** 的资深产品工程师与交互设计工程师。请在**现有仓库**中完成拾集 SHIJI V2 的视觉与动效升级，不是重新开发 App。

## 项目输入

- 仓库：`https://github.com/SilverLi123/shiji`；以当前工作区实际代码为准，不假定 GitHub 历史快照等于本地 HEAD。
- 已将设计资料放进仓库 `docs/shiji-v2/`，你必须先阅读：
  1. `docs/shiji-v2/IMPLEMENTATION_PLAN.md`：完整约束、分期、验收。
  2. `docs/shiji-v2/reference/motion-studio.html`：可交互概念 Demo，**只参考视觉、动效和交互感受，不可整体替换真实 UI**。
  3. `docs/shiji-v2/reference/desktop.png`、`mobile.png`：截图。
  4. `docs/shiji-v2/reference/walkthrough.mp4`：动效演示（环境支持时查看）。
- 概念视觉：深色编辑式素材画廊 + 紫色几何形变舞台 + Acid Lime 关键操作 + Kinetic Typography + 动画化分类/搜索/详情/收藏。
- 关键色：`#0c0d10` 背景，`#101115` 侧栏，`#15171d` 主面板，`#1d2027` 次级面板，`#f5f5f3` 文本，`#90919c` 辅文，`#d7ff65` 品牌荧光绿，`#a58cff` 品牌紫，`#79dfff` 点缀青色。

## 不可妥协的工程约束

1. **不要重写技术栈**：保留 macOS SwiftUI + WKWebView，桌面原生 HTML/CSS/JS + Python 标准库服务 + SQLite，iOS SwiftUI；不要为了 UI 升级强行迁 React/Electron/Flutter/FastAPI，不新增第三方运行时依赖。
2. **绝对保护现有用户数据、正式服务和协议**：不读写正式 `~/Library/Application Support/DevResourceLibrary` 数据，不接触已运行的正式 8782/8765 服务；QA 必须隔离临时数据目录与端口；SQLite/JSON schema 3、ZIP manifest 2、附件/备份格式不变；浏览器认证、局域网同步 TLS/证书 pinning、Keychain/配对/冲突处理不可削弱。
3. 保留项目、智能集合、复杂筛选、收藏/编辑/附件、批量管理、浏览器扩展、完整预览、备份恢复、回收站、Undo、iPhone 同步等现有功能。**不能把概念 Demo 的假数据、localStorage 保存方式或假异步解析接到正式 App。**
4. `desktop-app/static/app.js` 中卡片与资源状态是真实业务数据；`stable-cards.js` 已保证稳定节点与焦点恢复；`resource-bits.js` 已实现瀑布流的 FLIP、封面小幅 tilt 和 magnet；`liquid-glass.js` 有原生 Web 指示器。**必须复用或协调这些现成动画，不要堆第二套 transform/FLIP 与之冲突**。
5. 不要重新引入旧 `olla-motion.js` / `motion-decor`：已有 `test_liquid_glass.js` 显式禁止它们。为 V2 新建有独立命名空间的样式/动画模块，改动测试时只针对新增预期，不通过删除断言掩盖回归。
6. 动画不能影响焦点、可访问性、输入、滚动、缩略图缓存、键盘快捷键；`prefers-reduced-motion` / iOS `accessibilityReduceMotion` 优先，支持显式 `MOTION STUDIO / CALM` 切换、重播入场、动画取消和清理。Mac 原生 Liquid Glass 与 CSS 模拟玻璃不能混淆。
7. 不自动 push、不覆盖未提交的用户文件；若工作区脏，先汇报并采用不破坏用户修改的安全方案。新增代码配测试；按阶段提交或者留可审查的分阶段 diff。

## 开始前必须调查的文件

- `desktop-app/static/index.html`, `style.css`, `resource-bits.css`, `liquid-glass.css`, `app.js`, `stable-cards.js`, `resource-bits.js`, `liquid-glass.js`, `gallery.js`, `browse-controls.js`, `preview-ui.js`。
- `desktop-app/server.py`, `storage.py`, `capture.py`, `preview_jobs.py`, `desktop_service.py`, `desktop-app/desktop/*.swift`。
- `mobile-app/App/ShijiApp.swift`, `mobile-app/Shared/*.swift`, `mobile-app/ShareExtension/*`, `mobile-app/DESIGN.md`。
- `desktop-app/tests/test_stable_cards.js`, `test_masonry_batch.js`, `test_tilted_preview.js`, `test_liquid_glass.js`, `test_preview_jobs.py` 及其余相关测试。

## 请按顺序交付，不要只写设计提案

### 阶段 0 — 建立基线
- 调查当前 git status / 分支 / HEAD，工作区干净时创建 `feat/shiji-v2-motion-ui`。阅读现有设计和业务数据模型；确认原始测试通过与否，不要假设已通过。
- 确定文件修改清单、真实 UI DOM 挂接点、现有渲染/重排/焦点生命周期，写入简短执行计划。
- 所有截图、测试与服务运行使用临时 QA 数据，禁止触碰真实库。

### 阶段 1 — 视觉体系与桌面 UI（优先实现）
- 建立可维护的 V2 Design Tokens，建议 `static/shiji-v2.css`；让真实 Mac Web 工作区拥有 Demo 的深色侧栏、粗体编辑式标题、荧光绿主要操作、紫色几何 Hero、Kinetic Typography 横幅和沉浸式资源画廊。
- 不照搬 Demo 的 HTML 数据卡片；让现有 `render()`、`ShijiCards`、`ShijiBits` 和真实 SQLite 资源控制可视状态。Visual / Tool / Text 三类卡片从真实 kind/category 计算，图片优先显示真实封面，缺封面用原创类型识别占位。
- 保留当前两列真实瀑布流、列表和参考板、项目、智能集合、搜索、筛选、编辑抽屉、批量管理、附件、备份、回收站、快捷键和适配断点。大量资源时不牺牲性能。
- 不要复制演示假计数或假品牌资产。Hero 在主画廊才突出，回收站和操作页面以实用优先。

### 阶段 2 — 完整 Kinetic Motion（重点实现）
- 建立 `static/shiji-v2-motion.js` 等独立动效层，暴露 init/destroy 和明确 hooks，所有业务动作仍由原逻辑执行。
- 实现：①可跳过/重播的品牌入场（非阻塞）；②Hero 几何连续运动与细指针视差；③分类、排序和视图切换后的可控卡片重排 + 大标题瞬态；④与真实详情对齐的 shared-element 展开；⑤搜索聚焦与键盘操作；⑥收藏真实保存成功后的飞入/粒子反馈；⑦ Motion Studio/Calm 切换。
- **重要：** 分类重排直接协作 `resource-bits.js` 现有 FLIP/布局，不能重复给同一 `.resource-card` 的 `transform` 动画；已有 hover Tilt 仅作用于封面，不要对整个卡片再次倾斜。
- 动效需在 `prefers-reduced-motion`、触摸输入、关闭面板、快速连点、页面离开时正确清理；粒子和 ghost 有数量上限，GPU 友好的 transform/opacity 优先，不制造鼠标移动即 layout thrash。

### 阶段 3 — SwiftUI 原生体验统一
- Mac SwiftUI 宿主保留真实系统材质，统一品牌配色、图标与收藏动效，但不破坏 WKWebView / Python 服务绑定。
- iPhone 原生界面重做图库、导航、收藏控件、详情卡片，使其拥有同样的深色 Creative Tech 气质，并继续支持系统深浅色、Dynamic Type、VoiceOver、Reduced Motion、系统 Form、QuickLook、App Group 和同 Wi-Fi 同步。
- 不要把 HTML 全页塞进 iPhone WKWebView；不要改 iOS 的资源/附件/sync 的数据语义。
- iPhone Share Extension 空白页是仓库现有已知问题：若 UI 分期未处理，不要声称已修复，必须记录并给出独立修复建议。

### 阶段 4 — 真实快速收藏（UI 完成后单独实施）
- 为收藏入口提供 URL 快速输入，真实发起保存并让卡片及时出现。保存未完成只能显示“正在保存”；仅在后端返回成功后显示“已收藏”并触发动效。
- 保持既有去重、合法 URL 检查、异常与草稿恢复。后台元数据使用现有安全抓取路径；不要等待封面/网站截图阻塞收藏。
- 回填异步解析结果前检查资源 ID、URL、revision/guarded edit，不能覆盖用户手动编辑的标题、备注、标签、许可、附件。
- `preview_jobs.py` 默认关闭且至少 30 秒间隔是现行行为；除非专项设计和测试证明，否则不能擅自启用自动联网/截图、改变同步协议或增加远端服务。
- 离线手机也能保存本地 URL，无法补全时保持可用占位。

### 阶段 5 — 测试、真实 UI 验收与报告
- 每个阶段新增对应测试，并且运行已有测试：
  ```sh
  cd desktop-app
  python3 -m unittest discover -s tests
  npm ci --ignore-scripts --no-audit --no-fund
  npm test
  ```
- 运行 `cd mobile-app && python3 Tests/run.py --core-only`；环境具备时增加完整互通测试 `python3 Tests/run.py` 和 `python3 Tests/sync_integration.py`。
- macOS/Xcode 具备时运行 `cd desktop-app && python3 desktop/build.py` 及 iOS Debug/Release 构建；没有 Xcode 就明确说明未验证，不准宣称构建成功。
- 用真实应用 UI 截图/测试 1440×900、820×1180、390×844、340×740；至少覆盖空库、真实多资源、无封面、长中文标题、筛选、搜索、详情、选择、收藏成功失败、减少动态效果；如可运行 iOS 模拟器，再测浅/深色、Dynamic Type、VoiceOver 和同步入口。
- 给出真实录屏或截图与 `reference/` 并排比较。验收标准包括无横向溢出、无 JS 异常、不丢焦点、无残留 ghost、无误报成功、关键功能无回归、不会修改正式数据。
- 创建 `docs/shiji-v2/IMPLEMENTATION_REPORT.md`，列出：逐阶段完成清单、变更文件、真实测试结果、截图/录屏位置、性能观察、未解决问题、回滚步骤。

## 交付方式和沟通要求

请真正修改并测试源代码，不要停留在分析和 UI 建议。如果工作量较大，按上面严格串行分期，先完成可以运行/可验收的 P1+P2 桌面版，再推进 iOS 和 Quick Capture；**不要多个代理同时修改 `static/app.js` / `index.html` / CSS**。

每完成一个阶段，汇报：改了什么、修改的文件、运行的命令与真实结果、截图或预览路径、保留的限制、下阶段安排。对无法完成的验证如实说明。未经授权不推送远端，也不碰正式资源库。

现在请先读取设计参考与仓库，确认实际工作区和安全边界，给出简短实施清单，然后**直接开始阶段 0 / 1 的代码实现**。
