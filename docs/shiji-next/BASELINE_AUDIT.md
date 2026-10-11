# SHIJI Next — 分支与功能审查

2026-10-11，远端fetch后本地V5.2与远端均为 `b6c291347fc5429be7d93b93f6d40ddd92014949`，ahead/behind=0/0，工作树干净。沿用已隔离worktree `/Users/silver/shiji-card-restoration`，新功能分支 `feat/shiji-next-capture-organize`。新分支不追踪V5.2远端，避免误推旧基线；尚未推送或修改main。另一工作树 `/Users/silver/shiji` 的V2.1分支保持不动。

## 继承关系与PR

| 分支 | 当前远端提交 | 与前一项的关系 |
|---|---|---|
| main | 488d39e | 基础历史 |
| feat/shiji-v5-spatial-ui | 9d013bc | main后22个提交 |
| feat/shiji-v5-stable-beta | d7a6749 | V5后6个提交 |
| feat/shiji-v5.1-card-native-performance | 3d1928f | Stable后7个提交 |
| feat/shiji-v5.2-native-detail-performance | b6c2913 | V5.1后2个提交，仅QA/证据 |

逐项 `git merge-base --is-ancestor` 为true，无需重合并或cherry-pick已继承的修复。远端Stable与本地Stable无差异。

GitHub接口实查：唯一检索到的PR为 [Draft #1](https://github.com/SilverLi123/shiji/pull/1)，open、draft=true、merged=false，base为V5、head为Stable，并非main。V5.1/V5.2未发现PR。V5.2按提交查询的PR-triggered workflow runs为空；该API只查PR触发，不能据此断言所有CI没有运行。现有push过滤 `feat/shiji-v5-*` 不匹配V5.1/V5.2及Next新名称，本轮补覆盖，pull_request触发保持。

## 功能实际状态（源码与既有证据）

| 范围 | 已有实现 | 本轮应补内容 |
|---|---|---|
| iPhone分享 | 系统扩展入口、loading表单、URL/text/image provider读取、同App Group的LibraryFiles.capture、重复网址保护与备注追加；核心持久化已测 | 已知系统宿主空白页；真实Safari/文字/图片→保存→主App回读尚未通过。先区分启动、绘制、provider、容器保存 |
| Quick Capture | 先HTTP持久化，再metadata请求；revision和字段原值冲突保护、4槽限制，真实UI成功反馈 | 当前请求/线程级执行，不是持久后台任务队列；需任务状态、重启恢复、取消/重试/去重设计 |
| Preview | 默认关闭、单worker、间隔/暂停、og:image与Chrome fallback、真实封面不覆盖 | config持久于settings，但attempted/completed/failures仅内存；没有可靠任务进度/重启恢复。复用已有业务，不另建采集服务 |
| Search | desktop library.js：实际字段大小写折叠、空格分词AND/substring、丰富过滤；iPhone本地substring | 当前没有SQLite全文索引、相关性或匹配高亮。后续先评估中文trigram/分词支持、可重建侧车索引和schema约束，未提前选方案或改库 |
| Cover | V5真实图片优先与失效fallback，内容语义/稳定模板、3D和纯封面画廊；Art Direction Lab独立参考 | 尚无可同步的用户变体选择。先设计在schema3/manifest2兼容的持久化/交换方案，不能擅增列或将显示状态仅放localStorage |
| 管理/恢复/同步 | 收藏、编辑、精确标签、搜索筛选、项目/智能集合、附件、回收站/撤销、JSON/ZIP、备份预检恢复、HTTPS配对与同步 | 保留既有实现与回归；不得重复重写 |

V5.1的点击DOM稳定、占宽/日期、旧图片清理和Calm伪元素修复已包含。V5.2原生详情长帧仍未修复；其中缺少焦点的历史样本、竞争CPU和RAF自动点击条件不可被抹去。报告与原始数据原样保留在 `docs/shiji-v5.2/`，本轮不把该性能风险改写为已解决。

## 本轮fresh baseline

- Python全量208项通过，39.002s；Node52组通过。
- Swift核心、桌面manifest2 ZIP互通通过。
- 真实Swift↔Python临时HTTPS双向/附件/冲突/错误pin/迟到保存保护通过。
- V5.2 QA证据Python3项、Node1组通过。
- 独立App ID `local.silver.shiji.nextqa.app` / App Group `group.local.silver.shiji.nextqa`，新模拟器 `Shiji Next Share QA`；原生编译与运行验收分开记。

日志在 `evidence/baseline-*`。自动化覆盖schema3、manifest2以及未知资源字段原样保留的现有互通机制；它不证明系统分享绘制/真机签名/原生性能通过。

## 执行顺序

1. 独立基线/审查提交。
2. 扩展实际复现，记录启动/layout/provider/保存与App回读，根因最小修复加回归，单独提交。
3. Share专项达到可证明范围后，单独设计持久Capture任务。
4. 单独Search索引实验/性能与数据兼容方案。
5. 单独Cover持久化/同步设计与实现。

当前不开发3–5，也不重构首页、Hero或Motion系统。未具备真实运行证据的能力只记为编译/代码完成。
