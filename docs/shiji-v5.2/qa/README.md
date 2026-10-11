# V5.2 隔离性能 QA

这些脚本不被正式 HTML、Swift App 或 CI 产品构建引用。只使用临时目录、随机端口和一次性凭据。禁止将临时数据目录参数替换为正式库。

## 可重复运行

从仓库根目录：

```sh
python3 docs/shiji-v5.2/qa/make_native.py --count 1000 --tag v52baseline
```

复用V5.1 fixture生成器保存真实资源并制作ad-hoc临时App；元数据保存在 `/tmp/shiji-v5-stable-v52baseline-1000.json`。它不覆盖正式App。先结束编译，再用CUA或手工打开元数据中的App路径。执行真实卡片点击优先；QA快捷键 Command+Option+R 只用于 **自动化对照**。

QA自动输入只激活一次窗口、等已有资源和字体就绪，再等90个RAF让受控滚动稳定；普通event-task中触发 `.click()`。所有等待都在测试器，产品不受影响。冷启动每轮新WebView/WebContent，分别记录首/次详情，至少5轮。不要在1.1秒测量窗口中运行AX读、截图、录屏、编译或全量测试。原始数据包括点击focus、isTrusted、pointerdown/up、每次handler和RAF间隔。窗口occlusion日志来自QA-only原生诊断；正常App不调用私有进程PID API。

```sh
python3 docs/shiji-v5.2/qa/collect.py /ABS/TEMP/DATA/runtime-events.jsonl /tmp/v52-summary.json
python3 docs/shiji-v5.2/qa/test_trace_tools.py
node docs/shiji-v5.2/qa/test_probe.cjs
```

`validForeground`要求点击时非hidden、有focus、实际打开和非空RAF；`validPhysicalMouse`还要求可信click以及可信mouse按下/抬起。缺少字段的旧记录不默认合格。该资格是页面探针条件，不能代替系统级显示呈现测量或证明整个动画窗口没有失焦。

浏览器对照：

```sh
python3 docs/shiji-v5.2/qa/web.py
```

服务器创建临时Store并输出自己的端口/数据路径；QA按钮只存在该服务器。真实业务API与原始app.js负责保存和详情，不能用Demo/localStorage替代数据库。`?input-trace`额外输入日志单独分组，不混入静默基线。浏览器引擎、视口和渲染卡数须实际记录，不直接把浏览器当成原生WKWebView。

## Instruments

记录WebContent PID取自本次QA原生日志，确认进程存活且路径正确。`xcrun xctrace record --template 'Time Profiler' --attach PID --time-limit 25s --output /tmp/UNIQUE.trace`，待 recording started 后才点击。每次用绝对日志wallTime减trace起点对齐，不靠工具调用返回时刻推算。导出和分析另做，记录退出结果；错过点击或未成功结束的trace必须保留并注明无效。

`analyze_trace.py`用于单进程导出，`extract_process_trace.py`用于all-processes XML，显式提供本次QA PID与窗口：

```sh
python3 docs/shiji-v5.2/qa/extract_process_trace.py /tmp/profile.xml /tmp/qa-stacks.json.gz --pids HOST WEB --start 12.68 --end 14.30
```

全系统trace只留本机；共享GPU/WindowServer未确认独占时不作为App成本。inclusive栈采样权重有重叠，不能相加成wall-time阶段分解。

录屏复用V5.1 ScreenCaptureKit/AVFoundation工具，录制指定临时App窗口，不含音频；后续解码验证。视频输出帧率不等于App FPS。把录屏条件与静默基线分开。
