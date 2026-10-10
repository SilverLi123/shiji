# SHIJI V5.1 — Card Interaction & Native Performance

2026-10-10。基线 `d7a6749` / `feat/shiji-v5-stable-beta`；独立工作树 `/Users/silver/shiji-card-restoration`，开发分支 `feat/shiji-v5.1-card-native-performance`。开始时工作树干净。所有保存、恢复、配对和压力测试使用独立临时 Store/SQLite、随机端口及一次性凭据。正式资源库、用户未提交修改、main 和远端均未改动。

**状态：点击竞态和详情打开导致的画廊重排已修复，完整自动化通过；原生详情 >200ms 长帧仍未解决，不能标为性能验收完成或可发布。** V5 Hero、Spatial Deck、纯封面画廊、海报、560ms 连续展开、Studio/Calm 和 Space/Flat 保留；schema 3 / manifest 2、业务层和技术栈不变。没有新增运行时依赖或动画控制器。

## 问题定位与修复

### 1. 第一次点击丢失：元数据更新替换了按下的 DOM

复现：Quick Capture 真实持久化资源后，按住卡片，在 pointerdown 和 pointerup 之间释放异步元数据请求。原有 `ShijiCards.render()` 在 HTML 改变时替换整个 article；资源 ID 虽然相同，原始按钮及其父节点已脱离文档。WebKit 不向该按钮产生完成的 click。它不是依赖第二次点击才能工作的收藏业务。

修复：在现有稳定卡片渲染器内递归更新兼容的真实节点，以 action/id/value 或结构 class 匹配并保留按钮、父链和卡片。仍允许真实删除、排序、新增/移除封面及批量选择控件。相同地址的真实图片保留解码/失败状态；地址改变时更新图片。复用的 artwork 保留 IntersectionObserver 的 `art-in-view` 状态，避免元数据更新后静止。

验证：实际浏览器按住一次 800ms 的前后数据保存在 `browser-before-race.json` / `browser-after-race.json`。旧版没有 click/detail，新版原始点击打开详情。新增 Python→HTTP→SQLite→实际 app.js 的完整回归：正常表单先保存，受控元数据 fetch 在原始 pointerdown 后返回，实际列表重新渲染，然后原始按钮的一次 pointerup/click 打开真实详情；验证服务端仍为同一保存 ID 和更新后的标题。控制外网返回时机不替换持久化、API 或页面业务。

`capture-red.log` 是使用 d7a6749 稳定卡片代码的预期失败，`capture-green.log` 和最终完整 Python 测试通过。Node 还覆盖焦点、favorite、真实删除、图片/选择控件变更及 artwork 状态。没有补发第二次点击。

最终复核还发现并修复新节点更新路径的一个错误：更换图片地址时，原始图片已记为复用，但递归返回了新图片，旧 sibling 未删除。新增断言先得到2张图片而非1张的预期失败 (`cover-replacement-red.log`)，随后使用 `replaceWith` 清除原图，并验证原图脱离 DOM、只有正确新地址的一张图片。相同地址仍保留解码/失败状态，父按钮保持稳定。

### 2. 详情同步准备中的布局与日期初始化

实际 WebContent Time Profiler 已完成 20 秒记录。首个点击 2.8–4.2 秒采样窗口中，样式解析、layout/getBoundingClientRect、合成事务和 Intl.DateTimeFormat 初始化都有实际栈样本；cloneNode 在页面计时中接近 0ms。原始导出为 `xctrace-detail-profile.xml.gz`，分窗汇总 `first-detail-stack-window.json`。采样权重包含父子栈，不能相加成总耗时。

最小修改：复用一个等价的中文日期格式器；在启动 drawer 子元素 stagger 前读取连续展开的两个端点。仍由 ShijiMotion 管理同一代理、动画、取消和清理，不改动画时长或美术。

实际原生单次样本同步 handler 从 103ms 到 47ms，rect 从 55ms 到 34ms；原生后续仍有 252ms 帧间隔。它支持减少准备工作，不能证明整个首帧问题已经解决。新增 `test_v51_detail_reads.js` 对布局读写顺序及日期格式等价/单次初始化提供回归。

### 3. 锁滚动条使整个瀑布流重新布局

实际浏览器详情打开将画廊从 596px 扩到 604px，触发既有 ShijiBits ResizeObserver。一次 `layout()` 实测 87.1ms，随后出现 150.5ms 帧间隔。仅设置 `scrollbar-gutter:stable` 在当前 WebKit/定制滚动条环境没有避免宽度改变，因此没有把该尝试作为修复。

修复：第一次 openDrawer 在锁滚动前计算实际滚动条占宽，给 V5 body 预留同等空间；重复打开保留原值，成功关闭后清除。覆盖式滚动条为 0px。忙碌/未保存退出保护仍保留整个抽屉和锁。无需添加另一套布局或动画系统。

实际浏览器修复后 596→596，点击之后不再出现这次 ShijiBits 重排，除首次调度外的接下来七个 RAF 间隔最大 49.2ms。原生记录也保持 840→840。新增 scroll-lock 红/绿回归覆盖锁前测量、重复打开、释放、覆盖滚动条和保存保护。

### 4. 大 Hero 的 Calm 模式漏掉旧 CSS 伪元素循环

补充大 Hero 前台30秒采样时，真实原生诊断明确记录 Calm 下仍运行 `orb:hero-art shiji-brand-stage`；它是旧 CSS `::after`，不是有限 transition 或另一套 JavaScript 动画。修复只给既有有效 `body.calm` 状态下的 Hero 两个伪元素加暂停规则，Studio 仍保留品牌动效。现有 V5 Motion 回归增加实际 stylesheet selector 对两个伪元素、Studio 和系统有效 Calm 的检查；`calm-hero-red.log` 预期失败，`calm-hero-green.log` 通过。最终原生重开后 settled 的 CSSRunning=0 / running=0，随后30秒 profile 没有任何 CSS-running 项，p50/p95/max=17/18/49ms，见 `native-delivery-events.jsonl` 和 `native-calm-fixed-process.jsonl`。修复前与修复后的 Calm 采样分开保留。

### 5. 尚未解决：原生 WebKit 仍有较大首帧渲染成本

保持完整效果的原生样本仍有 243ms 帧间隔。将 AX 界面树读取推迟到展开结束后，仍有 249ms；该样本 handler 136ms、rect 93ms，说明准备成本也有波动。后续一次打开 212ms。不能只使用最小值报告改善。

仅在一次性 QA 副本进行的 no-blur、保留原生收藏 dock、Calm、关闭旧 drawer clip-path 动画、移除整页 inert、减少屏外 will-change 提示实验均没有消除原生长帧。所有实验已撤回，产品没有这些降级。坐标输入返回成功但没有 pointerdown，不能作为物理鼠标验证；已请求真实鼠标单次点击，交付时尚无完成回复。AX 按钮操作能实际打开资源，但仍需要真实输入对照。

最终补充的 12 秒 xctrace 在“ending recording”停留超过两分钟，已停止该已确认属于 QA 的工具进程；没有有效导出，不当作通过。前面的完整 20 秒采样和页面/进程原始数据仍保留。下一步应针对原生样式/首个 layer transaction 做有时间对齐的冷启动多轮 trace，以及有实际 GPU 归属的首个图层事务跟踪；在定位前保留可访问性和完整美术效果。

## 原生实际验收

一次只运行一个独立 App；编译结束后，分别采样 30 秒前台 Studio/3D 和 Calm/Flat。1000、5000 条数据来自实际 Store，画廊初始 60 个稳定节点。WebContent PID 从 QA-only WKWebView 诊断获取并与路径验证，而非根据 launchd 父进程猜测。该私有诊断 API 不进入正式 App.swift 或构建。

- 实际冷启动完成、关闭/重新打开窗口保持临时服务 PID，并重建 WebView、显示相同 5000 条资源。
- 实际原生上下滚动、五次详情开关、进入/退出全屏完成。关闭后代理归零、动画数有界；这不是 WebKit heap 泄漏认证。
- 实际可见性日志显示后台暂停/恢复；后台 CSSRunning=0 的记录保留。前后台切换时有限 transition 不等于持续循环。
- 真正睡眠/唤醒、真实物理指针、WebContent 故障恢复、多轮冷启动分布未完成。没有通过强制睡眠或结束无关 WebKit 进程替代验收。
- 没有修改 iPhone/Share Extension；真机签名、系统分享入口/App Group/局域网仍沿用已有报告的人工验收边界。

数值、条件、滚动长帧和内存归属见 [PERFORMANCE.md](PERFORMANCE.md)。不声称 60 FPS。

## 最终自动化和构建

在最后的滚动条修复之后复跑：

| 检查 | 实际结果 | 原始日志 |
|---|---|---|
| Python 全量 | 208 项通过，72.366s | evidence/final-python.log |
| Node 全量 | 52 组通过 | evidence/final-node.log |
| Swift 核心/桌面 ZIP | 通过 | evidence/final-swift.log |
| 真实 Swift↔Python HTTPS 同步 | 双向、附件、冲突、精确标签、错误 pin、迟到保存保护通过 | evidence/final-sync.log |
| macOS 原生构建 | 通过 | evidence/final-build.log |

基线为 207 Python / 49 Node / Swift 通过。全量回归仍包含存储、收藏、搜索筛选、真实封面优先/错误回退、详情、备份恢复、批量撤销、浏览器采集和同步；不是 Demo 模拟业务。Calm、系统 Reduce Motion、单 owner、快速取消/重开/teardown 由现有及新增 Node 回归覆盖。未改变测试超时来绕过失败。

## 改动与交付文件

业务修复：`desktop-app/static/{stable-cards.js,app.js,shiji-v2-motion.js,shiji-v5.css}`。

回归：`desktop-app/tests/{test_v51_click_identity.js,test_v51_detail_reads.js,test_v51_scroll_lock.js,test_stable_cards.js,test_v5_motion.js,test_v3_foundation.py,v51_capture_click.cjs}`。Swift 产品源码未改。

诊断工具：本目录 `qa/{web.py,trace.js,make_native.py,process_sample.c,record.swift,verify_video.swift}`，仅用于一次性 QA 服务/副本，正常 HTML 和原生构建不引用。证据包括原始 JSON/JSONL、完成的 Instruments 导出、测试日志及以下实际画面：

- [最终原生画廊](evidence/native-final-gallery.png) / [最终原生详情](evidence/native-final-detail.png)。均为 1000 条临时数据，带 QA 标记。
- [最终原生运行录屏](evidence/native-final-interaction.mp4)：大 Hero、进入画廊、单次打开/关闭详情、上下滚动。ScreenCaptureKit 录制指定 QA 窗口，无音频；请求28秒，实际视频29.78秒。AVFoundation 已验证视频轨道并解码0/8/16/24秒画面，见 `video-verification.json`；录制帧率不代表应用呈现 FPS。该录屏和最终截图在封面替换、Calm 两项补修后重新制作。
- [5000 条资源实际全屏](evidence/native-5000-fullscreen.png) / [窗口重开](evidence/native-5000-reopened.png) / [35 秒原生交互](evidence/native-5000-interaction.mp4)。这些在滚动条修复前、b2efa7a 代码下采集，不能误作最终首帧性能认证。
- [基线详情](evidence/native-before-detail.png) / [基线录屏](evidence/native-before-detail.mp4)。截图/录屏只证明实际界面，准确耗时来自单独原始日志。

本地提交按修复与证据分开；没有推送或合并。保留当前隔离预览供检查。剩余首帧性能风险必须继续调查，iPhone 分享扩展后续沿用 `docs/shiji-v5-stable/IPHONE_SHARE_PLAN.md`，不在本轮宣称已修复。
