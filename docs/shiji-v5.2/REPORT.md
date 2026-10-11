# SHIJI V5.2 — Native Detail Performance 调查报告

2026-10-11，开发分支 `feat/shiji-v5.2-native-detail-performance`，基线 `3d1928f`。**调查和测量工具已补全，原生详情长帧尚未修复；不能标为性能专项完成或可发布。产品源码仍与基线一致。**

## 已完成工作

读取V5.1报告、性能数据及既有动画/稳定卡片/App实现；先建立独立临时1000条Store数据库、随机端口、一次性同步环境。没有操作正式数据、配对凭据、main或远端；schema3、manifest2、Hero/Spatial Deck/海报、Studio/Calm、3D/Flat、560ms连续展开全部保留。

完成多轮新WebContent启动、首次/二次详情缓冲记录，以及点击对齐的单WebContent和Host联合Instruments采样。当前证据显示强制布局、样式解析及合成事务占有采样权重，DOM克隆没有成为主要已证实热点。尚未建立可以解释整个长帧的单一因果关系。

修正QA证据的三项可靠性问题：移除实时metrics DOM写入；重叠点击的结束回调保留各自handler，不错误写入最新点击；分开可见renderer、有焦点前台及可信鼠标资格。另补普通event-task输入对照，避免把RAF内自动点击当作实际用户事件。前台资格缺失的历史记录仍保留，明确降级，不删除慢样本。

原生坐标工具持续返回无可用窗口，但能读取AX和截图。AX/QA快捷键能实际打开页面，不能冒称物理鼠标。现已准备带点击焦点和原生occlusion日志的独立App，请用户直接点击卡片以完成真实输入对照。无需给正式App新增诊断接口。

## 实验结果与问题解释

没有通过缩短动画、去掉blur、缩小Hero或改变技术栈掩盖卡顿。root overflow、padding继承、opaque WebView、保持原生dock节点、content-visibility等单变量实验均未消除长帧，已从临时副本撤回。字体容器上下文的几何诊断没有出现source/ghost文字尺寸失配。

另一个预览页运行Studio造成CPU竞争；暂停该QA页后重新记录的5轮首次最大间隔中位数282ms、范围258–521ms。**这不是业务修复带来的改善**，且缺少点击焦点字段，不能作为合格前台性能结论。完整数据、采样边界、失败实验和Instruments时间对齐见 [PERFORMANCE.md](PERFORMANCE.md)。

## 自动化与构建实际结果

| 检查 | 结果 | 日志 |
|---|---|---|
| Python产品全量 | 首轮208项中3项临时HTTP连接拒绝；单独upgrade21项通过，完整复跑208项通过，40.854s | evidence/baseline-python.log、baseline-upgrade-retry.log、baseline-python-retry.log |
| Node产品全量 | 52组通过 | evidence/baseline-node.log |
| Swift核心/桌面交换 | 通过 | evidence/current-swift.log |
| Swift↔Python真实HTTPS同步 | 双向、附件、冲突、精确逗号标签、错误pin、迟到保存保护通过 | evidence/current-sync.log |
| macOS实际构建 | 通过 | evidence/current-build.log |
| QA证据Python回归 | 3项通过 | evidence/qa-regressions.log |
| QA缓冲Node回归 | 1组通过 | evidence/probe-green.log |

QA回归覆盖焦点/后台/空帧排除、可信click不能代替鼠标pointer序列、仅导出QA PID栈及引用解析、重叠点击归属。红/绿日志保留。它们验证测量器，不是原生性能修复回归。没有提高测试超时绕过首次Python失败；临时HTTP就绪竞争还需要独立复现才能认定原因。

## 实際运行证据与文件

- [原生调查录屏](evidence/native-investigation.mp4)，已解码验证；它是自动QA输入，不是物理鼠标视频。
- [原生详情画面](evidence/native-frame-8.png)，其余0/16/24秒帧也保留。
- `evidence/native-investigation-events.jsonl` / `native-investigation-summary.json`：所有运行，包括失败、慢样本和资格字段。
- `qa/probe.js`、`make_native.py`、`web.py`：仅独立临时环境；正式入口不引用。
- `qa/collect.py`、`analyze_trace.py`、`extract_process_trace.py`与QA测试：原始证据解析及资格判定。

首次测量基础已提交 `fe8922c`；后续诊断与证据单独本地提交。不自行推送、不合并。

## 下一步与剩余风险

当前必须先取得可信的原生卡片输入与焦点数据，再对各次rect/focus和首层合成作低干扰分解；基于该结果制作最小候选、红/绿回归及同条件5轮对照。尚无经过验证的产品性能修复。

新收藏立即打开、快速连续详情、1000/5000滚动、真实图片、搜索分类、前后台恢复仍需本阶段实际验收；已有自动化功能测试保留，但不能替代这些场景的原生实测。GPU实际归属、真实睡眠与长时间泄漏也未完成。

iPhone Share Extension下一阶段计划见 [IPHONE_SHARE_PLAN.md](IPHONE_SHARE_PLAN.md)，本轮未改iPhone或声称空白页修复。
