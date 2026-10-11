# 放在工具生态里看

OpenInquire 的交付是围绕主题形成的综合判断、来源和可继续使用的资料。平台连接、浏览器命令和媒体处理共同服务于这件事。

以下根据各项目在2026-10-11的公开README比较主打工作流；功能有交集，这是一张选用地图。

| 工具 | 主要交付与强项 | 我们吸收和组合的部分 |
| --- | --- | --- |
| [Agent Reach](https://github.com/Panniantong/Agent-Reach) | 为Agent配置多平台读取渠道，提供安装和状态检查 | 按渠道检查可用性，先用真实小样本确认读取层级 |
| [OpenCLI](https://github.com/jackwener/OpenCLI) | 可复用的网站命令、适配器与已登录浏览器操作 | 优先复用日常浏览器，把站内操作纳入调研 |
| [last30days](https://github.com/mvanhorn/last30days-skill) | 围绕近期主题收集社区讨论并综合 | 可选调用近期候选引擎，再读选中的原帖与评论；历史主题使用合适时段 |
| [dy-note](https://github.com/Rimagination/dy-note) | 将抖音视频转成带素材依据的学习笔记 | 字幕/转写、画面材料、笔记分开保存，按学习目的读取 |
| [Groundwork](https://github.com/SC-Airu/groundwork-skill) | 围绕需求、既有方案与实际反馈研究问题空间 | 比较人们怎样解决问题，以及宣传和实际使用中的差异 |
| **OpenInquire** | **围绕一个主题，组合中文平台经验、评论讨论、视频过程与技术来源，形成可追溯的判断** | **提供调研编排、技术社区只读MCP、本地视频助手、精简候选索引与连续调研约定** |

既有工具可以成为调研的一部分。OpenInquire 在选择来源、跟进评论、比较矛盾和整理结果这几步上提供统一工作方式。当前直接封装的可选上游检索引擎是 last30days；其他项目的设计借鉴或现有工具复用，不表示整套代码被打包，也不表示自动安装。

实际渠道与测试范围见[验收记录](verification.md)，组件关系见[安装说明](installation.md)。
