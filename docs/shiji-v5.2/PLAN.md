# SHIJI V5.2 Native Detail Performance — 最小实验计划

2026-10-11。基线 `3d1928f`，独立 worktree `/Users/silver/shiji-card-restoration`，分支 `feat/shiji-v5.2-native-detail-performance`。执行用户原生性能专项要求，不重构视觉。

## 约束与测量契约

不触碰正式库、配对凭据、main、schema 3 / ZIP manifest 2。保留 Hero、Spatial Deck、海报、连续展开 560ms、Studio/Calm、Space/Flat。只使用临时 SQLite、随机端口和 QA-only 注入；新增测试依赖不进入运行时。

- 固定 1000 条真实 Store 保存的 QA 资源、1180×820 初始窗口、Studio/3D；零外网依赖的生成封面用于首组排除图片解码。
- 5 轮新 WebContent/冷启动，每轮首次 + 第二次详情。保留原始时间戳、输入可信标记、每次 handler/布局读/克隆/动画准备以及完整 RAF 间隔，不丢弃慢样本。
- 轻量探针只在内存累积，结束后一次写日志。QA 的观察、日志写入、截图及 Instruments 条件分别标记；不在安静主样本中录屏/读取 AX。
- 安静样本后单独 trace WebContent、Host；若能确认专属 GPU PID，再采 GPU；共享进程不冒称 App 专属成本。
- CUA 坐标指针、AX 以及 QA 自动点击分组，检查 pointerdown/up/click 是否确实发生，不能把返回成功当成物理输入完成。

## 顺序

- [x] 基线全量 Python/Node 与环境/进程清单；建立只采样不改业务的 QA 副本。
- [x] 多轮可见 renderer 调查与点击对齐的 Instruments 分析（旧样本缺少点击焦点，前台资格未通过）。
- [ ] 隔离浏览器及物理鼠标对照。
- [x] 针对现有证据做单变量否证实验并撤回；尚未取得成功因果修复。
- [ ] 确认根因后写红/绿回归，最小业务修复；同条件 5 轮复测。
- [ ] 收藏后立即打开、快速重复/开关、滚动/搜索/分类/后台恢复、1000/5000 库以及 Calm/Reduce Motion 清理回归；实际原生录屏另采。
- [ ] 全量 Python/Node/Swift/同步/macOS 构建，报告原始数据、未完成事项和 iPhone 分享扩展下一阶段计划；本地分阶段提交，不自行推送。

## 重点复核

长标题/真实图与解码失败；详情在动画中更新；旧完成回调不能清除新代理；控件保持焦点/inert/退出保护；后台取消与恢复不残留无限循环。对应业务修复后增加回归，不用测试通过替代性能结果。

## 实验记录

初始 V5.1 探针会对每个事件更新 JSON script 并读取 getAnimations / computed style，可能影响样式、AX 与合成。先验证测量器干扰，不能把历史 249ms 全归因于探针。

基线复跑：52 Node 通过；208 Python 首轮出现3个临时服务连接拒绝，test_upgrade 单独21项通过，完整复跑208项通过（40.854s）。初始后台 AX 样本 hidden=true/无RAF，排除前台统计且保留证据。受控QA按钮在CUA返回后只激活一次，再等90个RAF让滚动/前台恢复稳定；该等待仅属于测量器，不进入产品，也不延迟真实卡片详情。测量为原生WKWebView实际自动化click（isTrusted=false），不冒充物理鼠标。

否证1：保留 root overflow 的QA实验仍516/398ms；否证2：body直接padding替代继承变量仍525/410ms。两项均不能解释主要长帧，撤回，不进入产品。有效25秒TimeProfiler的点击偏移16.268秒，16.26–17.1秒227样本，其中Main201ms；样式88、布局86、合成81、绘制21 inclusive ms，有重叠，不能相加。图片解码未命中分类，不能由此推广到真实图片。

测量资格修正：并行预览Studio的CPU竞争、RAF内自动click与缺少点击focus均已记录。hidden=false不得推断物理前台验收完成。收集器现分开可见renderer、有焦点前台、可信mouse序列；详情长帧未修复。完整否证、原始数据与验收边界见 REPORT.md / PERFORMANCE.md。
