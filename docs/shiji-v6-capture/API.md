# Smart Capture API 与任务生命周期

接口沿用本机服务的 Host／Origin 校验；浏览器扩展继续使用已有 `/api/clip` 配对认证。没有增加远程公开入口。

## 保存与后台补全

| 接口 | 实际行为 |
| --- | --- |
| `POST /api/resources`，`quickCapture: true` | 使用现有资源模型先保存；规范化重复 URL 返回已有资源，保留手工字段；资源与任务同一事务提交。该请求标志不进入资源数据。 |
| `POST /api/clip` | 先保存网页、选中文字和本地截图；远程 `imageUrl` 创建 asset 任务，不在收藏请求中下载。 |
| `POST /api/resources/{id}/enrich` | 保留兼容入口，参数仍为 `{url, updatedAt}`；现在只入队，返回任务和已保存资源。过期版本返回 skipped；自身补全后再次收藏复用原任务及状态，不因预期版本推进而新建任务。 |
| `GET /api/capture/tasks?limit=30&offset=0` | 全局计数与一页任务；limit 为 1–100，offset 为 0–1000000。拒绝未知、重复及无效参数。按创建时间倒序、ID 决胜排序，状态变化不会重排当前条目。 |
| `POST /api/capture/tasks` | 执行下表操作，返回默认首页状态；客户端在历史页操作后重新读取对应页。 |
| 既有 `/api/website-previews` | 仍是默认关闭、可暂停、限速的历史资源预览补全；执行进入同一任务表、同一个 Worker。关闭时读状态不创建任务。 |

任务状态响应含 `paused`、`active`、`counts`、`maxAttempts`、`tasks`、`total`、`offset`、`limit`、`hasMore`。counts 覆盖七种状态；任务页大小不限制全局计数。任务包含 ID、resourceId、type、url、resourceVersion、expectedRevision、attempts、nextAt、errorCode、error、创建／更新时间和整理建议。当前标题从真实资源读取，不复制一套资源内容。

| 操作体 | 约束 |
| --- | --- |
| `{action: "pause"}`／`resume` | 持久化暂停状态。暂停撤销运行租约并将其退回待处理，迟到响应不能写入。 |
| `{action: "cancel", id}` | 仅取消活动任务，保留已经保存的收藏与附件。 |
| `{action: "retry", id}` | 失败／取消后可重试，次数归零。URL 已变拒绝重试；资源版本已变则 skipped，不重新授权覆盖手工内容。 |
| `{action: "accept", id, updatedAt}` | 同时核对展示版本、任务预期版本和 URL；只填“其他”分类并追加建议标签，保留已有分类和标签。 |
| `{action: "ignore", id, updatedAt}` | 同样校验版本，持久标记忽略建议，不改变资源。 |

接受／忽略建议的错误不会关闭面板。历史任务始终可翻页查看；界面不提供对已过期 skipped 任务的强制覆盖按钮。

## 状态与恢复

`pending → running → completed` 是正常路径。临时网络／DNS／超时错误进入 retry，最多三次，重试间隔 5、10 秒；校验不通过、禁止访问等不可重试错误直接 failed。图片单独失败时，已解析元数据仍可保存，原收藏与海报继续可用。

running 带随机租约及 120 秒期限。在短 SQLite 事务中领取任务；网络和图片检查均在全局资源锁之外完成。提交前再次校验租约、暂停 generation、资源版本、URL、附件与封面。任何手工修改都优先，旧任务变 skipped。只有本任务事务产生的版本变化可推进同资源的兄弟任务，不能借此吸收用户编辑。

正常退出撤销正在执行的租约；进程强制结束后，重新启动及轮询恢复过期租约，最多等待剩余 120 秒，不立即抢占仍有效的其他进程租约。普通处理异常转为安全摘要并允许后续任务继续；进程／线程的灾难性终止仍依靠租约与下次启动恢复，不声称存在独立进程监督器。

## 元数据、图片、建议

提取 HTML／OG／Twitter 标题与简介、favicon URL、来源和 canonical 提示。保存的资源 URL 不因 canonical 改写；favicon 目前保存地址，不作为已下载附件。自动覆盖仅用于默认域名标题或空字段。

封面遵循人工封面／现存本地封面优先。新图片须经公网请求边界、5 MiB 限制、声明 MIME 与实际签名、尺寸／结构校验后才发布本地附件；同资源完整相同字节复用。PNG 校验 CRC、压缩流、行结构和必要调色板；JPEG 校验帧、编码表、扫描结构；JPEG／GIF／WebP 不等于完整像素解码。渲染解码失败仍由既有 V5 海报兜底。没有引入另一套海报引擎。

域名与内容规则集中于 `capture_rules.py`，输出现有分类和去重规范标签；建议存任务表，必须接受或忽略。当前涵盖 GitHub、React 组件、Hugging Face、动效、3D 素材与设计灵感，没有付费 AI API。
