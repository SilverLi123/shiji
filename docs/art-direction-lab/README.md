# SHIJI Art Direction Lab

独立的十二张封面美术评审板，延续现有 **Creative Tech Dark · Motion Studio**。当前是等待用户美术确认的候选表达；独立收尾结论仅为 **SHIP FOR STANDALONE USER ART REVIEW**，不代表用户接受、正式集成或产品发布。

## 启动与操作

从仓库根目录运行：

```sh
python3 docs/art-direction-lab/run.py
```

终端输出本次地址与临时数据目录。服务绑定 `127.0.0.1`，端口由系统分配，每次启动都用新的临时 SQLite 与既有 Store 保存十二条手动 QA 输入；不接收正式库路径。当前会话预览为 [Lab](http://127.0.0.1:54102/)，重启后以新输出为准。Ctrl+C 停止服务，临时目录不属于交付文件。

- **12 张设计板**：开发 3、设计 2、动效／3D 2、AI／ML 2、文章／代码／Prompt 各 1，逐张明确分配母版，不用 ID 哈希选择美术。
- **对照 Cover Studio 2.0**：同一保存记录左右对照；末尾提供 SHIJI 与 `3327d44` 卡片恢复版本的对照。旧 CSS 在 Shadow DOM 中将 `:root` 映射到 `:host`，使原始令牌生效。
- **V3 / V5 原始参考**：打开原始 HTML、查看用户提供的截图、手动播放原始视频。Demo 原有样例与存储只留在隔离参考页；不成为正式业务数据。
- **开启空间预览**：默认关闭，开启后用指针查看透视与前景位移；切换视图／后台会清理姿态，系统减少动态效果优先并禁用按钮。
- 地址加 `?phone=1` 可查看固定 **390 px CSS** 同源评审 frame。这是响应式网页检查，不是原生 iPhone 验收。

## 文件与真实来源

[BRIEF.md](BRIEF.md) 记录范围，[DIRECTION.md](DIRECTION.md) 记录 Lab 局部美术决定，[REPORT.md](REPORT.md) 记录实现、测试与证据，[REVIEW.md](REVIEW.md) 记录独立收尾意见。

`run.py` 创建并保存手动输入；`lab.js` 从 `/lab-data` 读取保存结果后生成十二个明确母版；`lab.css` 只定义此评审页面。网站名称与链接对应真实来源，字段不声称来自抓取。代码和 Prompt 展示实际保存内容。Poly Haven 使用仓库已有网站截图，其余物体为自绘 CSS／SVG；曲面和张量切片明确标为抽象研究，不是 AI 输出。无远程字体、外部 AI 或新增运行时依赖。

原始参考位于 [`../shiji-v2/reference/v3-poster-lab/`](../shiji-v2/reference/v3-poster-lab/) 与 [`../shiji-v2/reference/v5-spatial-poster/`](../shiji-v2/reference/v5-spatial-poster/)，六份 HTML／PNG／MP4 字节一致性记录见 [reference-sha256.txt](reference-sha256.txt)。[REFERENCE_README.md](REFERENCE_README.md) 保留提供者说明，其中早期下载步骤是历史说明；本机已取得并复制文件。

## 验证与证据

本轮执行结果详见 REPORT：Lab Python **2 项通过**，JavaScript **12 母版与实际资源 DOM 检查通过**，既有 Node **40 组通过**。文档整理没有重复运行这些测试。基线 202 项 Python 没有在本轮重跑，Swift 没有重建。

复现 Lab 检查：

```sh
python3 docs/art-direction-lab/test.py
NODE_PATH=/Users/silver/shiji/desktop-app/node_modules node docs/art-direction-lab/test.cjs http://127.0.0.1:54102/
```

JavaScript 命令的地址应替换为本次启动输出；`NODE_PATH` 指向现有含 `jsdom` 的测试依赖目录，不是 Lab 运行时依赖。

| 查看内容 | 证据 |
| --- | --- |
| 完整十二张板、手机单列 | [desktop.jpg](evidence/desktop.jpg)、[mobile.jpg](evidence/mobile.jpg) |
| 同资源前后对照 | [comparison.jpg](evidence/comparison.jpg)、`evidence/pair-01.jpg` 至 `pair-12.jpg` |
| SHIJI 恢复版本完整对照 | [restoration-comparison.jpg](evidence/restoration-comparison.jpg) |
| 空间预览指针两帧 | [spatial-left.jpg](evidence/spatial-left.jpg)、[spatial-right.jpg](evidence/spatial-right.jpg) |
| 原始参考与现场运行 | [reference-comparison.jpg](evidence/reference-comparison.jpg)、[v3-running.jpg](evidence/v3-running.jpg)、[v5-running.jpg](evidence/v5-running.jpg) |

桌面观察到的 CSS 视口为 1412 px；手机 frame 为 390 px。IAB 图像输出分别缩放为约 1375／382 px 宽，不能以截图像素替代 CSS 视口。空间证据为静帧，没有新增 Lab 录屏；V3／V5 原视频分别约 14.56／29.16 秒。没有实测 FPS、WCAG 全量验收或原生 iPhone 结论。

## 审批与保留边界

先由用户确认美术，再决定生成规则与正式集成。此板仍有明确参考差距：矢量材料不及 V3 球体／金属环的塑形光照；指针透视加前景平移没有实现 V5 完整分层 Z 深度、Spatial Deck 或连续循环。

本轮范围只含 Lab 与两份原始参考目录。正式 Hero、品牌动画、ShijiBits 卡片动效 owner、业务流程、SwiftUI、schema 3、ZIP manifest 2 保留；不创建新生成引擎，不合并或推送 main。既有 `desktop-app/DESIGN.md`、`PRODUCT.md` 与 `.impeccable/design.json` 均保持原字节，Lab 说明不升级为正式设计令牌。
