# 隔离验收

从仓库根运行 `python3 docs/shiji-v6.1-capture/qa/serve.py`，创建临时 Store、随机端口和名为“拾集 V6.1 QA · 临时资源库”的扩展副本。状态保存在 `/tmp/shiji-v61-qa.json`，一次性配对只写入临时副本，不使用正式凭据。浏览器工具禁止打开扩展管理页，需用户手动加载该路径。

手动扩展验收：收藏普通页面／选中文字／截图；关闭仅该 QA 服务后收藏，看到等待发送；重启同一数据目录与端口后等待或重试；确认同一请求只保存一次。更改到另一个临时配对后，旧记录应 blocked。当前服务准备脚本每次创建新库，重启同库时必须显式使用已有状态，不可误把重新创建的新库当作中断恢复。

自动化恢复场景在 `desktop-app/tests/test_extension_delivery.py`：三个独立 Node 进程使用生产队列与传输模块，真实 HTTP、真实 Store；覆盖离线暂存、丢响应、Store 重开、回收站和回执。它不能证明 Chrome 已安装或 MV3 alarm 在真实浏览器触发。

`prepare_phone.py` 仅在名为 Shiji Next Share QA 的已启动模拟器创建独立 `local.silver.shiji.v61qa.app`／`group.local.silver.shiji.v61qa` 工程副本。工程与输出路径见 `/tmp/shiji-v61-phone.json`。

构建使用仓库既有 README 的模拟器参数：`ARCHS=arm64 ONLY_ACTIVE_ARCH=YES CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- CODE_SIGNING_REQUIRED=NO`，然后运行 `python3 mobile-app/Tests/check_bundle.py <临时 Shiji.app>`。不得用 `CODE_SIGNING_ALLOWED=NO` 的无权限输出替代可安装分享包。

安装到该命名 QA 模拟器后，通过真实 Safari／系统分享选择“拾集 V6.1 QA”。`check_phone.py` 只读核对隔离 App Group；`--require-safari` 要求实际保存的 example.com URL；`--snapshot`／`--unchanged` 可核对取消前后字节。它不创建收藏，也不触发分享，不能作为 UI 执行器。

实际截图放到 evidence，敏感配置、SQLite、配对码和构建目录仅留在临时目录。
