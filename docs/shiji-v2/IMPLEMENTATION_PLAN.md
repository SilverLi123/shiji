# 拾集 SHIJI V2 — Creative Tech Dark · Motion Studio 实施方案

> 编制：2026-10-08  |  面向仓库：https://github.com/SilverLi123/shiji  
> 仓库审查基线：`main` / `488d39ef948ccba920bcf0edbee9bd9e6d6beb0c`（开始实施时重新确认 HEAD）。  
> 目标：将概念演示的 **品牌视觉、布局和动效语言** 安全移植到现有 macOS + iPhone 应用，不破坏资源、存储、同步、备份和采集。

## 0. 使用方式 / Reference of truth

当前目录包含：
- `reference/motion-studio.html`：已可独立运行的概念 Demo，可用浏览器直接打开体验动效；**仅作为视觉与交互参考**。
- `reference/desktop.png`、`reference/mobile.png`：桌面和手机截图，用来比对布局、色彩与密度。
- `reference/walkthrough.mp4`：实际操作录屏；重点看入场、分类重排、详情展开、快速收藏反馈。
- `CODEX_MASTER_PROMPT.md`：可直接交给 Codex 执行的详细指令。

**优先级：真实产品功能、原始数据安全和可访问性 > 设计规范与动效统一 > 像素还原 Demo。** Demo 使用虚构样例、localStorage 和模拟异步收藏，不能替代生产 API；不能把 Demo HTML 当主页面覆盖 `desktop-app/static/index.html`。

## 1. 现有产品架构核对

| 现有模块 | 当前实际实现 | V2 处理原则 |
|---|---|---|
| macOS 宿主 | `desktop-app/desktop/*.swift`：SwiftUI、WKWebView、原生操作浮层 | 保留容器和真实 macOS 26+ Liquid Glass，低版本保留原生材质回退 |
| Web UI | `desktop-app/static/index.html` + `style.css`、`resource-bits.css`、`liquid-glass.css` + 原生 JS | 增加 V2 token / 主题 / 动效模块，渐进改造真实 DOM |
| 渲染和瀑布流 | `static/app.js`、`stable-cards.js`、`resource-bits.js`；稳定节点、焦点恢复、按资源 ID 更新 | 保留 keyed 节点、图片解码复用、短列瀑布流与现有列表 / 参考板 |
| 搜索/筛选/预览 | `browse-controls.js`、`gallery.js`、`filter-editor.js`、`similar.js` 等 | 不删除能力；保持已有快捷键、选择、完整图与附件预览 |
| 桌面本地服务 | `server.py`、`desktop_service.py`，Python 标准库 HTTP 服务 | 不换 FastAPI、不更改服务协议、端口和认证；现有端口 8782 |
| 数据存储 | `storage.py` + SQLite / 本地附件、备份、恢复 | 不改 SQLite / JSON schema 3；不改 ZIP manifest 2 |
| 网页元数据 | `capture.py` 的安全抓取 + `/api/metadata` | 保留安全策略；后续可以异步封装，不可引入任意 URL 读取内网风险 |
| 后台封面 | `preview_jobs.py`，默认关闭，间隔至少 30 秒 | UI 不擅自改变用户隐私/联网偏好；任务调整另做独立变更 |
| 手机端 | `mobile-app/App/ShijiApp.swift` + `Shared/`、`ShareExtension/` | SwiftUI 原生实现同一视觉语言；保留本地库和系统操作习惯 |
| 双端同步 | `desktop-app/sync_transport.py`、`mobile-app/Shared/SyncClient.swift` 等 | 不动 TLS、配对、证书校验、冲突协议；无云同步 |

**特别注意现有测试的契约：** `test_stable_cards.js` 依赖稳定真实卡片节点与焦点恢复；`test_tilted_preview.js` 保证倾斜只作用于图像且 touch/辅助功能回退；`test_masonry_batch.js` 约束批量布局性能；`test_liquid_glass.js` 明确不复活旧的 `olla-motion.js`/`motion-decor`。V2 应使用新、独立的命名空间，而不是简单重新链接旧 Olla 动效代码。

## 2. 设计规格（可直接落成 tokens）

### 2.1 设计方向

**Creative Tech Dark × Motion Gallery**：深色编辑式画廊 + 紫色创意几何品牌 + 荧光绿关键操作 + 技术工作台的信息秩序。

主色基于真实演示：

| 设计令牌 | 值 | 用途 |
|---|---|---|
| `--shiji-bg` | `#0c0d10` | 画廊主背景 |
| `--shiji-sidebar` | `#101115` | 左侧工作台导航 |
| `--shiji-surface` | `#15171d` | 操作容器 |
| `--shiji-surface-raised` | `#1d2027` | 悬浮面板与按下态 |
| `--shiji-fg` | `#f5f5f3` | 主文字 |
| `--shiji-muted` | `#90919c` | 次级文字，具体字号需校验对比度 |
| `--shiji-line` | `rgba(255,255,255,.095)` | 精细分隔线 |
| `--shiji-lime` | `#d7ff65` | 主操作、选中状态、视觉品牌 |
| `--shiji-violet` | `#a58cff` | 品牌舞台、几何插画 |
| `--shiji-cyan` | `#79dfff` | 技术信息、链接与辅助强调 |
| `--shiji-ease` | `cubic-bezier(.22,1,.36,1)` | 大部分平滑过渡 |

字族：系统字体优先；英文可使用本机 Inter / SF，中文 PingFang SC / Noto Sans SC；**不强制下载付费字体或远程字体**。英文标签可用字间距和小号大写，中文要保证小屏可读。桌面标题约 40–64px，正常标题 24–32px，卡片标题 16–20px，正文 14–16px，辅助信息 12–13px；iOS 改用 SwiftUI 动态字体而非复制像素值。

### 2.2 设计原语

- **Brand geometry**：一种基础收藏符号 + 紫色动效舞台 + 荧光绿几何碎片，不套用他人商标。
- **Dark gallery**：封面优先、低边框感；真实封面优先，缺封面采用 CSS/SVG 类型识别，不伪造资源内容。
- **Three card archetypes**：Visual（图片与实际网页截图）、Tool（GitHub/网址，来源和描述更重要）、Text（代码/提示词，采用可阅读的文字摘要）；实际资源映射到已有 `kind` / `category`，不写死演示数据。
- **Editorial header**：大标题 + 品牌几何舞台。仅在适当的主资源视图显示；其他列表、回收站、管理界面优先实用。
- **Contextual actions**：搜索、过滤、预览、收藏、批量操作是可发现的；不能为了视觉省略原有控件。
- **Accent restraint**：不要让荧光绿覆盖所有按钮，主要用于 1 个主操作及少量关键状态。警告/错误继续用可区分的语义色。
- **Native distinction**：CSS `backdrop-filter` 不等于原生 Liquid Glass；macOS SwiftUI 控件在支持系统用真实系统材质，网页阅读层保持清晰；iPhone 同理。

### 2.3 响应式与内容

- ≥1280px：完整侧栏 + 编辑式 Hero + 两列稳定瀑布流；保持既有 `data-gallery-columns=2` 真实布局契约。
- 760–1279px：侧栏可抽出，Hero 缩排，工具条能换行；分类横向滚动。
- ≤760px 的网页预览：手机式导航与单列内容排布可做模拟，但不应被当成 iOS 原生 App 的源码。
- iPhone：Native `NavigationStack` + `TabView` + 系统搜索 + `LazyVStack`，大图与无封面卡片不同密度；系统分享、文件选取、QuickLook 与同步页面仍使用原生能力。
- 340/375/390px：无横向溢出、无被遮挡按钮；44pt 可点击尺寸，动态字号与 VoiceOver 可用。
- 用户收藏超多时：保留已有每次 60 条“继续浏览”机制、全部筛选语义、无封面/破图回退及快速滚动。

## 3. Motion System 动效规格

| 场景 | 目标效果 | 建议实现与时长 | 性能/可访问性边界 |
|---|---|---|---|
| 初次进入 | 荧光绿短暂幕布 + SHIJI 品牌字 + 几何压印 | CSS clip/transform + WAAPI；约 0.9–1.45s，总体非阻塞 | 只在首次展示或用户点“重播动效”，不影响真实数据加载；可跳过 |
| Hero 品牌形状 | 连续轻量旋转/形变、鼠标视差 | CSS transform 与 pointer 位置映射；低频 | 后台、面板打开、低性能和 Reduced Motion 下暂停 |
| 卡片筛选/排序 | 保留卡片从旧位置移动到新位置，新卡片错峰进入 | **复用 `ShijiBits` 当前 FLIP/瀑布流生命周期**；320–550ms | 不能在同一节点叠加两套 transform 动画；不重排 1000 张不可见卡片 |
| 卡片 Hover | 真实封面轻微 3D 倾斜与局部光缘 | 120–200ms；最多 ±3°；只对细指针 | 保留现有 `tiltPoint`，禁用于触摸/键盘 focus、破图、完整预览 |
| 详情打开 | 封面通过临时代理无缝延展到实际详情区域，内容错层出现 | WAAPI 约 450–700ms；原 DOM 的详情及时可用 | `pointer-events:none`，代理动画结束必删除，Esc/焦点保持 |
| 收藏成功 | 几何碎片/短距离飞入 + 卡片高亮 | 成功**写入 SQLite 之后**触发约 450–900ms | 不伪报保存成功；失败保留 URL/草稿，提供重试 |
| 搜索 | Spotlight 风格放大/聚焦，结果淡入 | 180–320ms | 焦点自动定位到输入；Esc 还原原焦点，键盘完整可用 |
| 项目/导航切换 | 精简的大字瞬态 Stamp + 内容重排 | 250–550ms | 不遮挡交互，不依赖动画传递唯一信息 |
| 反馈与状态 | 轻量 beacon、按钮 feedback 与 toast | 120–250ms | 保留明确文字；不靠颜色单独区分状态 |
| iOS 控件 | `.spring` / `.matchedGeometryEffect` / 原生过渡 | 约 250–500ms | 尊重 `accessibilityReduceMotion`、Dynamic Type；不复制网页无限动画 |

**模式：** `MOTION STUDIO`（默认强动效）与 `CALM`（精简动效）通过界面显式切换；网页用单独的 UI 偏好键（如 `shiji-v2-motion-mode`）保存，不写入资源数据库；系统 `prefers-reduced-motion: reduce` 一律优先于 Studio；iOS 以 `accessibilityReduceMotion` 优先。`prefers-reduced-transparency` 和高对比度需要可读的实色回退。

**性能预算（验收目标，非目前实测）：** 常见 Apple Silicon 机器中，UI 动画尽可能保持 60fps；优先 `transform` / `opacity`，不能在每次 `pointermove` 大范围改布局；限制代理卡片/粒子数量；关闭弹层取消动画，注销监听和 observers；1000 条数据的布局成本仍不随新 Motion 模块呈不受控增长。首次可交互不等待开场动画；无 JS 错误或严重长任务。

## 4. 实施路径（严格串行，阶段完成才继续）

### P0 — 安全基线 / 范围确认

1. `git status --short`，确认工作区状态；新建 `feat/shiji-v2-motion-ui` 分支，不覆盖未提交的用户改动。
2. 查阅 `README.md`、`desktop-app/APP.md`、`desktop-app/DESIGN.md`、`mobile-app/DESIGN.md`、`static/index.html`/`app.js`/`resource-bits.js`/`stable-cards.js`、SwiftUI 主界面、相关测试。
3. 使用隔离 QA 数据目录和独立端口（不可触碰 `~/Library/Application Support/DevResourceLibrary`、原服务 8782、8765、真实 iPhone 库或配对凭据），记录基线测试、截图和当前限制。
4. 列出真实现有功能清单，形成 V2 改造前后逐项回归表。

验收：基线记录齐全，正式数据零写入，仓库提交/文件范围可追溯。

### P1 — 视觉令牌与桌面 Shell

- 新建 `desktop-app/static/shiji-v2.css`：仅定义 V2 token、排版、侧栏、Header、Hero、工具栏和表单/详情的视觉，避免覆盖旧样式后又被层叠反覆盖。
- 在 `index.html` 追加明确的 V2 CSS 与脚本，抽取 Hero/品牌舞台的 DOM；优先保持原有 ID、`data-action` 和功能结构。
- 在 `app.js` 的真实状态和 `render()` 里注入实际数量、当前筛选、导航状态，不塞硬编码“8 条样例”。
- 在画廊样式里覆盖颜色和展示层级，不破坏 `resource-bits.js` 的绝对定位、图片比例和既有瀑布流/完整图/列表/参考板模式。
- 维持现有侧栏项目、智能集合、回收站、备份、导入、批量操作入口；“新设计没有展示的旧功能”必须保留在清晰可发现的位置。

验收：真实空库、真实多媒体、无封面、长标题、各种筛选都可用；桌面不同宽度截图与概念稿同气质。

### P2 — 品牌 Motion 与交互层

- 新建 `desktop-app/static/shiji-v2-motion.js`（可附对应 `shiji-v2-motion.css`，不要复活旧 `olla-motion.js`）。只负责**动效编排**，不拥有资源业务数据，也不直接写数据库。
- 暴露小而清晰的 API，例如 `init({document,window})`、`beforeListUpdate()`、`afterListUpdate()`、`openDetail({resourceId,sourceElement,detailElement})`、`captureConfirmed(...)`、`setMode(...)`、`replayIntro()`、`destroy()`；API 以实际现有渲染生命周期适配。
- **特别约束**：当前 `ShijiBits` 已经做了有限 FLIP、图片 tilt、magnet。不要再加第二套相同功能导致 transform 叠加。重排动画优先扩展现有模块或显式协调生命周期；只在需要的关键动作引入新强动效。
- 搜索、分类、详情、收藏与 toast 的现有事件处理仍通过当前 `app.js` 主逻辑；motion 只订阅明确的已完成事件。捕获必须使用真实 `/api/resources` 保存结果触发，而不是按钮一按就显示“成功”。
- 为 `MOTION STUDIO / CALM` 与「重播入场」增加可发现控件和键盘/ARIA 状态；遵守操作系统动效偏好。

验收：6 大交互动效可用，打断时不会留下 ghost DOM、禁用浮层或输入焦点丢失；已有相关测试全绿。

### P3 — 原生 macOS 和 iPhone 视觉统一

- macOS：SwiftUI 原生采集浮层与 Web 侧的品牌配色、图标和反馈一致；macOS 26 原生 `glassEffect` 和早期系统材质 fallback 继续有效；不要把 CSS 玻璃等同于原生材质。
- iOS：将同一品牌 token 翻译为 SwiftUI / Asset Catalog semantic colors；重做 `GalleryView`、`ResourceCard`、收藏浮层、详情；保留 `NavigationStack`/`TabView`/`QuickLook`/原生 Form；设计重点是深色的沉浸感、大图展示及轻量几何动效，而不是将 Web 整页嵌进 iPhone。
- 支持浅色/深色系统语义适配或明确的 App 外观设置，不要以固定黑色导致低对比度/系统 Form 冲突；参考 demo 暗色为 V2 主视觉。确认 Sync、备份与权限页面仍可读。
- 仍保留分享扩展源码；**当前分享扩展空白页是已知独立缺陷**，不能因 UI 美化宣布它已修复。若本阶段未修复，记录为 blocking backlog 并在 QA 准确说明。

验收：iPhone 浅/深色、动态字号、VoiceOver、基础分享和同步入口无回归；原生 Debug/Release 构建可复现。真机未测就明确写“未验证”。

### P4 — 真实 Quick Capture 动效与异步补全（功能增强，单独受控）

优先完成 UI/动效，不因本阶段导致大范围后端改动。接入时：
1. 用户粘贴 HTTP(S) URL，立即在 UI 展示**正在保存**占位；调用已有 `/api/resources` 真实写入；成功后才显示“已收藏”、触发飞入反馈。
2. 对于尚无标题的资源，使用 URL hostname/repo slug 作为临时名称；同 URL 重复收藏遵守既有去重/409 语义，不产生副本。
3. 元数据使用已有安全的 `capture.py` / `/api/metadata` 路径；建议在真实保存后**异步**丰富元数据，并确保只有未被用户手动修改的目标字段才回填。必须通过已有 guarded-edit / revision 判断，防止后台覆盖人工编辑、附件、许可等字段。
4. 网页封面补全沿用 `preview_jobs.py`：默认关闭、每次 ≥30 秒的联网/截图任务策略不要未经确认改动；如引入持久队列，需要独立测试重启恢复、失败重试、暂停、限流、取消和数据安全。不能把“后台补全耗时”强行耦合到保存完成提示。
5. iPhone 完全离线时能本地保存并显示可用占位；不能暗中要求手机运行 Python 或突然引入云账号。与 Mac 的补全可在明确同步边界内发生。

验收：快速写入、延迟元数据、错误/超时、重复收藏、并发人工编辑、不联网、App 重启等路径均安全；失败可恢复、不损坏资源。

### P5 — 整体验收与文档

1. Python 回归：`cd desktop-app && python3 -m unittest discover -s tests`。
2. 前端回归：`cd desktop-app && npm ci --ignore-scripts --no-audit --no-fund && npm test`（npm 仅开发测试，不加到 App 运行时）。
3. 手机核心/互通：`cd mobile-app && python3 Tests/run.py --core-only`；环境允许再运行 `python3 Tests/run.py`、`python3 Tests/sync_integration.py`。
4. macOS/Xcode 可用时运行已存在的构建脚本 `cd desktop-app && python3 desktop/build.py` 及 iOS scheme 构建；若环境不具备 Xcode，明确说明“未验证”，不能宣称通过。
5. Web UI 截图/自动化：1440×900、820×1180、390×844、340×740；检查初始、分类切换、搜索、收藏、详情、空库、图片失败、选择/批量、Reduce Motion。至少录一段 10–20 秒真实动作视频以便设计对照。
6. Native UI：尽可能使用模拟器检查 iPhone 深浅色、Dynamic Type、不同屏幕、VoiceOver / Reduce Motion；保留可靠截图和测试日志。
7. 在 `docs/shiji-v2/IMPLEMENTATION_REPORT.md` 记录变更文件、成果截图、完整测试结果、已知限制、回滚命令。对手工/外部依赖说明来源与许可，不能提交用户个人真实收藏和凭据。

## 5. 功能与安全红线

- 不删：项目嵌套 / 智能集合 / 组合筛选 / 列表与参考板 / 全图预览 / 媒体播放 / 导入导出 / ZIP / 恢复 / 回收站与撤销 / 备注 / 标签 / 编辑冲突 / 浏览器扩展采集 / 手机局域网同步。
- 不改：SQLite / JSON schema 3、ZIP manifest 2、默认端口 8782、桌面服务数据目录、浏览器扩展认证与来源检查、TLS & pinning & Keychain、64MB 附件约束。
- 不增：无必要的第三方运行时依赖、云服务、登录功能、远端素材抓取、假许可证/价格。
- 不写：真实数据目录、持久服务端口、正式配对凭据、手机生产数据；测试数据只在临时目录。
- 不许：用 Demo 的 localStorage / 硬编码样例替代现有 `Store`；制造“一点击即成功”假反馈；仅为通过测试而删除既有测试；覆盖不相关的用户修改。
- 动效不会影响：可访问性焦点、键盘输入、VoiceOver、低动态偏好、可交互时间、媒体解码复用或滚动性能。

## 6. 建议交付顺序与提交

- `feat(v2): add design tokens and dark editorial shell`
- `feat(v2): integrate motion orchestration with existing gallery lifecycle`
- `feat(v2): style native mac and ios surfaces`
- `feat(capture): connect quick-save feedback to persisted result`
- `test(v2): cover motion, accessibility, persistence and viewport regressions`
- `docs(v2): implementation report and visual evidence`

**每阶段都要可运行可回滚；P1 / P2 / P3 / P4 严格串行执行，尤其 `static/app.js` / `index.html` / CSS 文件不允许并行智能体相互覆盖。** 未获得用户明确授权不推送远端、不改主分支。

## 7. 视觉验收表

- [ ] 桌面第一眼与 `reference/desktop.png` 在深色布局/荧光绿/紫色品牌氛围上相符（非像素复制）。
- [ ] 手机真实 Native 与 `reference/mobile.png` 共享视觉语言，且 Dynamic Type 可用。
- [ ] 首页品牌动效可以跳过/重播，首次交互不被挡住。
- [ ] 分类真正重排，卡片按实际数据库内容渲染，保持当前选中项、焦点和图片状态。
- [ ] 详情代理正确清除；搜索焦点和 Esc 返回正确。
- [ ] 收藏成功反馈只在持久化成功之后出现；错误不吞草稿。
- [ ] 动效模式切换、系统 Reduced Motion、Reduced Transparency / 高对比度可用。
- [ ] 所有既有高级功能入口仍能找到；无数据丢失、schema/manifest 变更。
- [ ] 无 console error、横向溢出、长时间主线程卡顿；测试和截图有确切记录。

