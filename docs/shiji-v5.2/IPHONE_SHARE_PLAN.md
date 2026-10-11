# V5.2 后续 iPhone Share Extension 专项

本文件是实施计划，尚未执行，不把构建通过当成分享功能通过。沿用 `docs/shiji-v5-stable/IPHONE_SHARE_PLAN.md` 的隔离约束。

1. 建立独立QA Bundle ID、App Group与临时存储，检查实际安装扩展的principal class、签名/entitlements、共享容器读写。无有效开发团队时明确真机阻碍，不改真实配对凭据或正式库。
2. 从真实Safari、文本及照片分享入口启动，采集viewDidLoad/appear/layout、NSItemProvider和保存阶段OSLog；区分扩展未启动、视图尺寸/hosting问题、共享容器拒绝、provider加载失败。先定位再最小修复。
3. 验证URL、纯文本、图片与文件字节，覆盖离线、取消、重复分享、超限、provider失败和重试；每个故障恢复要有可见错误或安全取消。
4. 验证成功持久化后才completeRequest，主App能读到相同稳定资源ID、原始逗号标签和附件；取消不改数据，异步补全不覆盖手工编辑。
5. 实际验收深浅色、大字号、Reduce Motion、窄屏与QuickLook，然后在隔离同Wi-Fi环境验证同步。录制从系统分享入口到主App出现资源的完整链路。

交付定位、回归、真实模拟器/真机录屏、签名边界与未完成事项。V5.2原生性能调查结束后再开始，不混入当前产品性能实验。
