# V5.2 原生详情性能调查数据

2026-10-11。基线 `3d1928f`，产品代码尚未修改。以下是定位数据，不是修复后的性能认证。使用临时 SQLite / 随机端口、1000 条由真实 Store 保存的 QA 资源、生成海报封面和原生 WKWebView。首组无网络图片，不能推广到真实图片解码成本。窗口名义尺寸 1180×820；网页视口以每条原始记录为准。

## 测量资格与污染因素

RAF 间隔是相邻 JavaScript 回调实际执行时间的差，包含同步处理、布局、渲染调度与系统负载；不是 GPU 实际呈现 FPS。首个间隔从 click 捕获开始计算。完整间隔保留，不删除坏结果。

发现并纠正三个测量问题：

1. 旧探针在页面 DOM 中不断序列化指标；V5.2 改为内存缓冲、动画窗口结束后一次输出。仅 QA 副本加载。
2. 较早“单原生 App”样本期间，另一个 Codex 预览标签页仍运行 Studio 动效，曾观察到其 Renderer 约108% CPU。随后关闭新测试标签，将原有 QA 预览暂置 Calm，再重复采样。不能把前后差异全归因于产品代码。
3. `document.hidden=false` 不等于有焦点的前台交互。旧样本缺少点击时 `document.hasFocus()`，不得标为已合格前台样本。当前收集器分开标记 `visibleRendering`、`validForeground` 和 `validPhysicalMouse`；真实鼠标还要求可信 click、可信 mouse pointerdown/up。原生坐标工具返回无可用窗口，目前需要手工卡片输入对照。

另一个偏差：早期 QA 自动点击在第90个 RAF 回调中调用 `.click()`。有效 Instruments 栈也确认 `JSRequestAnimationFrameCallback::invoke` 来源。新增普通 event-task 对照，零延迟定时器仅把 QA 输入移出 RAF，不改变产品动画或真实点击时机。一次 event-task 样本仍683ms，不能据此说触发时机是已证实根因。

## 原始产品的多轮自动化样本

下表为原始 V5.1 产品代码，无截图/AX读取/录屏/编译发生在测量窗口内；依旧是 `isTrusted=false`，旧探针缺少点击焦点字段，因此仅作为可见 renderer 调查数据。详情都实际打开，结束后代理为0。按 `native-investigation-summary.json` 的运行16–20对齐。

| 冷启动轮次（Host / WebContent） | 首次 handler / 最大间隔 ms | 第二次 handler / 最大间隔 ms |
|---|---:|---:|
| 95125 / 95138 | 64 / 260 | 46 / 255 |
| 95651 / 95663 | 48 / 258 | 63 / 282 |
| 95981 / 95992 | 57 / 282 | 48 / 228 |
| 96580 / 96590 | 62 / 340 | 86 / 433 |
| 96976 / 96980 | 127 / 521 | 108 / 402 |

首次最大间隔中位数282ms（258–521）；第二次282ms（228–433）。同步 handler 中位数首次62ms、第二次63ms。长帧未消失，尚无修复前后对照。此前运行1–5首次中位数456ms（354–542），受并行预览影响，保留原始记录但不混合统计。

运行21的普通 event-task：handler205ms，其中 rect165ms，最大间隔683ms。探针焦点字段在该轮之后才增加。新资格字段的后续运行见原始日志和汇总，不与旧5轮拼为同条件统计。

## 已完成且点击对齐的 Instruments

### 单 WebContent Time Profiler

`/tmp/shiji-v52-web-detail.trace`，有效25秒。开始时间 `2026-10-11T12:14:00.321+08:00`，点击偏移16.268秒；分析窗口16.26–17.10秒，227个采样，主线程201ms权重。

| 分类 | inclusive 采样权重 ms |
|---|---:|
| 样式计算 | 88 |
| 布局 | 86 |
| 合成 | 81 |
| 绘制 | 21 |
| 可访问性 | 5 |

父子栈重叠，不可相加为 wall-time。图片解码分类未命中，仅说明本次生成封面样本没有该分类，不证明所有图片成本可忽略。该轮有 profiler 和并行预览条件，不纳入安静基线。原始导出 `detail-time-profile.xml.gz`，窗口分析 `detail-trace-window.json`。

### Host 与 WebContent 联合 Time Profiler

`/tmp/shiji-v52-all-detail.trace` 已正常完成，开始 `2026-10-11T12:29:58.531+08:00`，总长32.543秒，点击偏移12.690秒。保留12.68–14.30秒内明确属于 QA 的 Host91907、WebContent91912栈：`joint-qa-stacks.json.gz`。

Host主线程122ms权重，WebContent主线程306ms权重。WebContent 中实际出现 `getBoundingClientRect` / `updateLayoutIfDimensions...`、样式解析及 layer transaction；Host 出现 WebKit / QuartzCore / SwiftUICore / AttributeGraph。Host 的 SwiftUI120ms大部分是主 run-loop 父栈，不能说它是120ms独占 SwiftUI 绘制成本，更不能由此认定收藏 dock 根因。`joint-module-summary.json` 提供 inclusive 与 leaf 分开统计。

完整 all-processes trace 与79MiB导出留在本机临时目录；仓库只存选定 QA PID 栈，避免混入其他应用的调用栈。共享 GPU / WindowServer 尚不能可靠归属于本 App，不声称已测得 App 总图形成本。

较早 `/tmp/shiji-v52-web-baseline.trace` 在点击1.218秒之后才开始，明确错过首帧；其 idle 导出保留并标记无效首点击证据。进程 `sample` 也未可靠对齐，不当作根因依据。

## 单变量否证实验

全部仅在一次性 QA bundle 中进行，均已撤回，产品未包含这些改动。

| 假设 / 实验 | 实际最大间隔 ms | 结论 |
|---|---:|---|
| 保留 root overflow | 516 / 398 | 未消除长帧 |
| body直接padding代替继承变量 | 525 / 410 | 未消除长帧 |
| 原生 opaque drawsBackground | 1026 | 未消除长帧 |
| 原生收藏 dock保留节点、隐藏显示 | 780 | 未消除长帧 |
| cover art content-visibility:auto | 480 | 未消除长帧 |

容器查询失去上下文的假设：原生 source/ghost字体均43.684px、宽268px，浏览器两者均47.4014px，未出现预想的文字放大差异。额外 computed style读有干扰，984ms诊断样本单列，不用于改善统计。这些单次否证不能证明属性一般无害，也不能作为有效性能修复。

## 实际画面

`native-investigation.mp4` 是指定隔离 App 窗口的 ScreenCaptureKit 实录，实际30.797秒、1180×820、视频名义29.440帧/秒。AVFoundation已解码0/8/16/24秒。录制帧率不是 App FPS。QA 快捷键触发自动详情，视频不能当作物理鼠标验收。录制期间一次打开handler170ms、最大间隔494ms，另一次65/316ms；记录和安静样本分开。

## 尚未通过的验收

- 原生物理鼠标、可信焦点下多轮首次详情对照。
- 精确定位单个强制布局与首个 layer transaction 的因果关系；目前只有栈证据，未有成功最小修复。
- 本阶段真实图片解码/错误回退、5000条滚动、搜索分类、连续真实操作和后台恢复的新实测。V5.1记录属于旧阶段，不标成V5.2新通过。
- GPU专属归属、真正睡眠恢复与长期泄漏验证。

后续先取得合格输入，再在同条件下拆分各次布局读与首次合成。失败方案不进入产品，仍保留完整560ms连续展开和全部视觉。

补充输入诊断：运行23的AX单击产生trusted=true，但pointer=null、hidden=true、focus=false且没有RAF。详情实际打开、handler691ms/rect405ms；该后台样本不计入前台性能或物理鼠标结果。这也验证了不能仅凭isTrusted或AX返回成功判断真实鼠标完成。窗口已留回画廊，等待手工对照。
