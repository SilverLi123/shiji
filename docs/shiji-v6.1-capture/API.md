# V6.1 Capture Everywhere：接口与兼容性

## 手机同步入队

`SyncEngine.commit` 仍接收协议 1。原有版本校验、附件不可变性校验、请求回执和资源事务保持；附件安装后，仅为新增或 URL 变化且未删除的网站调用既有 `enqueue_capture`。删除撤销旧租约；普通整理不会重新排队。重放同步请求优先返回原回执，不重新覆盖后台补全。

后台产出的标题、简介和本地封面仍由既有快照及附件下载返回手机，不新增同步字段。实际 Swift URLSession HTTPS 测试覆盖手机上传、电脑解析 Fixture、真实 PNG 附件下载和手机回读。

## 浏览器可靠提交

| 接口 | 行为 |
| --- | --- |
| `POST /api/clip/ping` | 既有连接探测新增 `captureReceipts: 1`。 |
| `POST /api/clip/status`，`{requestId}` | 返回 `{requestId,status:"not_found"}` 或 `{requestId,status:"saved",resourceId}`。需要原有配对认证与本机 Host／扩展 Origin 校验。 |
| `POST /api/clip`，可选 `requestId` | 请求 ID 为规范小写 UUID。资源、附件、后台任务和回执同事务保存。成功响应包含 `receipt`。 |

同 ID、同内容重试直接返回回执和当前资源，保留后续编辑及回收站状态；资源缺失时 `resource` 为 null，回执仍为 saved，不创建替代资源。同 ID 不同内容拒绝。无 requestId 的旧客户端保留原行为。

回执表 `clip_receipts(request_id,payload_hash,resource_id,created_at)` 为本机派生状态，不包含网页正文、截图或凭据，没有改资源模型。`PRAGMA user_version=3`、ZIP manifest 2、手机同步协议 1 均保持。

## 扩展恢复

浏览器 `chrome.storage.local` 保存冻结的 payload／请求 ID／配对指纹／状态／尝试次数／下次发送时间。每次发送先探测能力，再查回执；仅 not_found 时 POST。未确认成功会保留原内容，重启后继续核对。最多 100 条，8 MiB 准入预算中为状态变化预留空间；错误文本有界。最近 100 个确认结果仅用于弹窗反馈，不代替电脑端永久回执。

网络使用单个发送循环，单轮最多 3 条。Chrome alarms 每分钟唤醒，空队列撤销 alarm；Worker 启动时重建丢失的 alarm。浏览器休眠／退出不保证即时发送，恢复后继续。官方参考：[alarms 生命周期](https://developer.chrome.com/docs/extensions/reference/api/alarms)、[storage 配额及访问级别](https://developer.chrome.com/docs/extensions/reference/api/storage)。

配对指纹由规范 base 和 token 的 SHA-256 生成；token 不逐条复制。地址或配对码变化会阻止旧队列发送，只有连接原配对才允许重试。配置权限限制到可信扩展上下文。旧电脑端不支持回执时不盲发，提示更新。

状态为 pending／sending／failed／blocked。sending 期间不允许移除；如果发送循环已结束但存储失败留下发送标记，允许恢复或移除。移除待发送不撤销可能已经到达 App 的收藏，界面有明确说明。

## 备份、回退与边界

- JSON／manifest／手机同步不携带回执。原始 SQLite 快照自然包含可选表；manifest 恢复仍只恢复既有资源与附件，不导入凭据或派生回执。
- 在原目录内恢复不会主动清除现有回执。恢复到新库时凭据变化会阻止旧扩展队列误投；不保证跨人工复制凭据后的 transport 去重。
- 回退到 V6 可忽略额外表。V6.1 扩展会在旧服务上保留待发送并要求升级；需要同时回退扩展时，应先处理尚未发送内容。
- 当前回执不自动清理，以保留重试去重依据；长期历史治理留待后续专项。扩展卸载会移除浏览器本地待发送记录。
- 文件发布与 SQLite 间的已有崩溃切点、原生首次详情长帧、实体设备验收仍沿用既有风险，不因本轮网络回执通过而消除。
