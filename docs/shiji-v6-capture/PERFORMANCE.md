# V6 Capture 性能记录

测量于 2026-10-14，交付整理于 2026-10-15。macOS 26.6.2 arm64、Python 3.9.6、SQLite 3.51.0；浏览器为 Codex 内置 Chromium 155。全部为临时库与合成 QA 内容，通过真实 Store／API 保存，不是 Demo 的 localStorage 数据。

## 后端

`python3 docs/shiji-v6-capture/qa/benchmark.py` 创建 1000／5000 条资源，每项 25 次采样。分别测全资源 state、30 条任务状态查询、领取任务＋本地 HTTP Fixture 请求＋真实 PNG 校验／本地附件提交。Fixture 网络成本不能代表外网站点。

最终原始数值见 [backend-performance.json](evidence/backend-performance.json)。该文件保存每次样本及 P50／P95／最大值；测试数据库和附件留在 JSON 指定临时目录。任务调度以一个 Worker 顺序执行，页面查询不等待网络解析。

| 最终后端 P95 | 1000 条 | 5000 条 |
| --- | ---: | ---: |
| 全量 state | 53.644 ms | 95.118 ms |
| 30 条任务状态 | 5.293 ms | 21.573 ms |
| 领取／Fixture 解析／附件提交 | 29.970 ms | 11.832 ms |

最终采样与独立 100 URL 恢复测试并发运行，宿主还有其他进程，不能称作安静环境。较早一轮数据保留在 [backend-performance-initial.json](evidence/backend-performance-initial.json)；两轮干扰条件不同，不用于宣称优化前后加速。最终采样在图片、分页及快照审查修复后运行。

## 浏览器实际输入

QA 复制生产静态文件，仅附加被动探针，未模拟点击、替换业务数据或启动第二个动效控制器。探针在首次 `shiji:rendered` 后等待两个 rAF，记为“首个资源画面呈现代理”，不是标准化 TTI。搜索／分类从实际输入事件量到同一绘制代理。源代码见 [observer.js](qa/observer.js)。

| 指标 | 1000 条 | 5000 条 |
| --- | ---: | ---: |
| 首个资源画面代理 | 553.6 ms | 1481.8 ms |
| 搜索单条匹配 | 16.8 ms | 67.9 ms |
| 清除搜索 | 79.9 ms | 239.6 ms |
| 分类切换 | 121.4 ms | 262.4 ms |
| 启动后 rAF 样本数 | 1155 | 1039 |
| rAF P50／P95 | 16.7／17.1 ms | 16.7／33.3 ms |
| 最大帧间隔 | 416.9 ms | 249.8 ms |
| 大于 50 ms | 4 次 | 15 次 |

每个数据规模只有一轮页面导航和上述三个输入，不能据此声称稳定 60 FPS 或提供可靠输入 P95。帧探针只记录启动后约 20 秒的可见页面，混合初始化与静置，不是独立滚动测试；测试环境并非安静原生性能环境。完整摘要见 [ui-performance-summary.json](evidence/ui-performance-summary.json)，原始帧数组保留在 `/tmp/shiji-v6-ui-1000.json` 和 `/tmp/shiji-v6-ui-5000.json`。

## 原生与剩余风险

实际隔离 SwiftUI＋WKWebView App 显示 1000 条资源；原生搜索 `QA 00999` 后网页匹配数降至 1，任务数量为 975，截图见 [macos-1000.png](evidence/macos-1000.png)。这证明原生宿主能加载真实业务和搜索，不等于原生队列面板／帧性能已完整验收。

原生工具多次在弹层鼠标输入返回无可用窗口，另有超时及浏览器连接恢复；用户解锁并置前后截图和原生搜索成功，弹层点击仍未完成。本轮没有新的可信 WebContent/GPU／CPU／内存归属采样或 Instruments 性能结论。

V5.2 首次详情约 243–249 ms 长帧仍未定位为已修复，完整沿用 [V5.2 报告](../shiji-v5.2/REPORT.md) 和 [原始性能记录](../shiji-v5.2/PERFORMANCE.md)。5000 条前端仍加载并筛选全量数据，Search 2.0 应继续处理这一成本；本轮没有以缩小 Hero、删除连续展开或降低海报质量掩盖它。
