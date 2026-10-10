# V5.1 实测数据与验收边界

macOS 26.6.2 / 25G83，ARM64；真实 WKWebView 原生 App 和隔离 Codex WK 浏览器。数据为独立 SQLite 中明确标记的 Store 压力资源，不使用正式库。记录的是仪器数据，不能转换成 GPU 实际呈现 FPS。不同运行的系统/缓存/启动状态有差异，全部是单次采样，不能推出统计上的性能改善百分比。

## 首次详情

| 原生步骤 | 同步 handler | rect 部分 | 前八个 RAF 间隔 (ms) |
|---|---:|---:|---|
| 基线 d7a6749 | 103 | 55 | 152, 265, 160, 37, 4, 16, 16, 17 |
| 端点先读 + 日期复用 | 47 | 34 | 58, 252, 166, 13, 11, 10, 16, 18 |
| 再保留滚动条占宽 | 63 | 39 | 67, 243, 17, 16, 17, 16, 18, 16 |
| 最终版本、延后 AX 界面树读取 | 136 | 93 | 175, 249, 16, 17, 16, 17, 17, 16 |

原始 `native-{before,minimal,lock,final}-events.jsonl`。按每个文件最后一次 webview.create 后的第一次 click-start 对齐；原始文件含早先实验/重开，不能把多段日志拼成一次启动。第一间隔从 click-start 到首个 callback，后续间隔为相邻 callbacks，包含 handler、合成、调度等；QA 仪器和 AX 输入也有开销。最后一次补充 Instruments 在另一轮 warm 打开中未有效结束，不能作为该表的采样栈证据。

仍有 243–249ms 原生间隔，不标记首帧修复通过。QA-only 去除 inert 的实验仍为278ms、去除屏外 will-change 提示仍为361ms，均撤回；这些独立单次样本不证明各属性有害或无害，只说明实验没有消除问题。clone 约 0ms，不能把复制 DOM 主观认定为主要瓶颈。已完成 20 秒 Time Profiler 导出中，2.8–4.2 秒首点击窗口为 333 个约 1ms 样本：resolveStyle 91ms、updateLayout 45ms/rect 44ms、buildTransaction 32ms/compositor 32ms、IntlDateTimeFormat 初始化 18ms、AX copy hierarchy 22ms。这是 inclusive sample 权重，重叠栈不能相加，并非精确 wall-time 分解。原始 gzip 导出及窗口汇总可复查。

浏览器中确认的布局缺陷：锁滚动导致 596→604px，既有瀑布流重排 87.1ms；仅加 stable gutter 的 QA 实验仍发生。实际占宽修复后 596→596px，点击之后没有再次调用这次布局。前八帧为 91.36,16.64,49.2,17.6,16.6,31.4,18.6,16.7ms。首次 handler 75.3ms，不能忽略它或把后七帧称为整体首帧通过。见 `browser-gutter-first.json` / `browser-lock-first.json`。

## 单 App 前台 30 秒 RAF

补充最终 renderer/滚动锁版本的实际大 Hero 前台采样（Calm 伪元素修复前）：

| 模式 | 时长 | 间隔数量 | p50 / p95 / max ms | >33.34ms 次数 | WebContent CPU / 峰值 footprint |
|---|---:|---:|---|---:|---|
| Studio / 3D | 30.005s | 1776 | 17 / 18 / 129 | 11 | 0.843% / 292.47MiB |
| Calm / Flat | 30.010s | 1800 | 17 / 17 / 46 | 1 | 0.213% / 238.25MiB |

独立原始文件 `native-final-hero-{studio,calm}-process.jsonl`，实际 CPU 区间分别30.174/30.106秒，从 QA 按钮启动 RAF 后开始，因此与 RAF 窗口相近但不完全相同。Host CPU0.142/0.057%，Python0.037/0.032%。测量时大 Hero 在视口中，没有 AX 读取、编译或测试。该 Calm 采样明确发现一个旧 `::after` orb CSS 循环，已定位并补暂停规则，见报告；不能将该修复前数据说成完全静止模式。

Calm 补修后的独立原生复验：大 Hero 在视口，settled cssRunning=0 / running=0；30.011s RAF1798个间隔，p50/p95/max=17/18/49ms、超过33.34ms两次，profile结束没有 CSS-running 项。实际30.096s进程区间，Host/WebContent/Python CPU=0.053/0.208/0.035%，WebContent峰值/结束footprint=230.58/207.53MiB。原始 `native-calm-fixed-process.jsonl`、`native-delivery-events.jsonl`。这证明遗漏的 CSS 循环被暂停，两个不同运行的内存/CPU差不能全归因于此修复。

先前的画廊前台采样：

| 实际库 | 模式 | 采样时长 | 间隔数量 | p50 / p95 / max ms | >33.34ms 次数 |
|---:|---|---:|---:|---|---:|
| 1000 | Studio / 3D | 约30s | 1800 | 17 / 18 / 30 | 0 |
| 1000 | Calm / Flat | 约30s | 1799 | 17 / 18 / 25 | 0 |
| 5000 | Studio / 3D | 30.004s | 1778 | 17 / 18 / 185 | 4 |
| 5000 | Calm / Flat | 30.017s | 1777 | 17 / 18 / 86 | 3 |

1000 采样发生在最小准备/滚动条修复前；5000 发生在 b2efa7a、滚动条修复前。它们是各版本独立对照，不是假装全部为最终版本，滚动条修复不影响静止画廊的样式。QA 按钮激活窗口后启动，之后不执行 AX 读取、截图、编译或其他测试，只有进程采样；hidden=false。原始数据为 `native-before-events.jsonl` / `native-5000-events.jsonl` 中 profile-end。

5000 前台实际上下滚动的三个短窗口：

| 间隔数量 | p50 / p95 / max ms | >33ms |
|---:|---|---:|
| 68 | 17 / 21 / 49 | 3 |
| 53 | 17 / 41 / 136 | 4 |
| 63 | 17 / 38 / 192 | 5 |

不要计入另一个 hidden=true 的滚动窗口。滚动由 CUA 原生 scroll 完成，有 AX 状态读取与工具开销，窗口短；idle 的 p95≈18ms 不证明长列表滚动流畅。5000 条仍只渲染初始 60 卡片，全库可搜索/筛选。实际首次 render 826ms、render 工作323ms（从 QA 脚本开始计，不是进程冷启动时间）；重开会缓存变化，未做多轮冷启动分布。

## CPU 与实际内存归属

使用 `proc_pid_rusage(RUSAGE_INFO_V4)` 每秒保存原始 user/system 纳秒、resident、physical footprint。CPU 是区间时间差 / 实际 elapsed ×100，表示一个 CPU 核心的百分比；1000 早期采样没有 monotonic 时间字段，用名义30s，标为近似。5000 使用实际30.088/30.150秒。RSS 不包含所有压缩内存，physical footprint 不等同 RSS。

| 数据/模式 | Host CPU % | WebContent CPU % | Python CPU % | WebContent 峰值 / 结束 footprint MiB |
|---|---:|---:|---:|---|
| 1000 Studio | ≈0.118 | ≈0.939 | ≈0.023 | 272.49 / 268.28 |
| 1000 Calm | ≈0.065 | ≈0.271 | ≈0.031 | 228.03 / 211.45 |
| 5000 Studio | 0.126 | 0.969 | 0.081 | 292.66 / 276.20 |
| 5000 Calm | 0.062 | 0.266 | 0.092 | 269.84 / 269.84 |

5000 Studio 结束 Host footprint38.88MiB、Python33.53MiB；Calm39.24/27.58MiB。完整各 PID、路径、peak/end footprint、resident 和 elapsed 见 `process-summary.json`；原始四个 `native-*-process.jsonl` 保留，不只留汇总。WebContent 通过实际 WKWebView QA 进程诊断确认，不通过 parent PID 推断。

共享 GPU / Networking / WindowServer 不能从当前采样可靠分配给单个 App，所以不包含它们，也不称这些数字为 App 全部图形内存或总能耗。低平均 CPU 同样不消除短时间 >200ms 长帧。

## 清理与后台

实际 5000 数据原生连续五次打开/关闭后，settled ghosts=0，动画条目有界，未看到单调增长。现有取消、连续打开、reduce/Calm/destroy 测试通过。只验证有限轮 DOM/动画资源清理，没有 heap snapshot 或长时间泄漏认证。

关闭窗口的 lifecycle 实测保存 backend，重开重新构建 WebView。实际全屏进入、菜单退出、visible↔hidden 事件和后台 CSSRunning=0 有日志。动画总 running 项包含有限 transition，不能据一个瞬间总数直接判断循环；本轮用 CSSAnimation 分类和名称定位到 Calm 的旧 Hero orb，确认为持续循环并修复。

未完成：真实鼠标对照、真正睡眠/唤醒、真实 WebContent 异常恢复、多轮冷启动统计、GPU 专属归属。补充 Time Profiler 12s 执行未得到有效导出，保留工具日志并明确不计入完成采样。不得由构建通过推导这些场景通过。
