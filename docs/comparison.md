# OpenInquire 与同类工具

**抖音、小红书、B站和公众号的专门读取流程，是 OpenInquire 的重点。** 它组合日常浏览器、平台适配器与视频处理，针对登录、动态页面、图文和视频选择读取方式；取得材料后，再与海外社区讨论、开源代码和技术原始资料对照，服务于选型、选题、想法验证和既有工作比较。

## 从工具能力，到你要完成的事

| 对比对象 | 官方文档中的主要能力 | 做专题调研时还要处理的工作 | OpenInquire 的对应能力 |
| --- | --- | --- | --- |
| [Agent Reach](https://github.com/Panniantong/Agent-Reach#为什么需要-agent-reach) | 多平台读取接入、安装配置、渠道诊断和后端选择 | 围绕问题组织证据，追踪作者修正，将不同来源整理成可用结论 | 主题拆解、评论深读、反例查找、引用与综合交付 |
| [OpenCLI](https://github.com/jackwener/OpenCLI#opencli) | 通用浏览器操作、站点命令、适配器开发与已登录会话复用 | 决定查什么、读到什么程度、如何对照多站材料 | 用 Skill 驱动跨站研究，将网页操作接到问题分析、视频材料和来源笔记 |
| [last30days](https://github.com/mvanhorn/last30days-skill#sources-scored-by-the-people) | 近期主题发现、评论与视频转写、社区信号评分和综合；公开来源表以 Reddit、X、YouTube 等为主 | 针对国内社区增加站内深读路线，将热点线索放回历史背景和实际实现中核对 | 小红书、知乎、公众号、抖音、B站专门路线；按主题选择时间范围，衔接代码、论文与原始资料 |
| [DyNote](https://github.com/Rimagination/dy-note#核心特点) | 抖音视频、评论、账号与话题分析，转写、画面补证、资产复用 | 将抖音里的结论带到其他平台验证，形成跨来源的专题判断 | 围绕同一问题联查文章、问答、视频和开发者讨论；本地助手处理已取得的媒体 |
| [Groundwork](https://github.com/SC-Airu/groundwork-skill#what-it-does) | 用英文搜索扫描问题空间，分析现有解法、使用方式、矛盾和缺口 | 继续进入中文站内材料，读取视频过程，并持续跟进已有研究 | 中文平台深读、多模态材料、原始来源与未决问题留存，下一轮继续推进 |

上述比较核对于 **2026-10-11**，依据各项目公开 README 的默认工作流。OpenInquire 的流程由 Skill、宿主 Agent 与已连接的工具共同执行；各渠道当前可读范围见[实测记录](verification.md)。

## OpenInquire 的特点

- **中文内容平台有专门方案。** 抖音、小红书、B站和公众号各有搜索与深读流程，按内容选择浏览器、平台 MCP、正文提取或视频处理；[首页列出具体做法](../README.md#难接入的平台我们怎么读)。
- **来源广。** 中文平台与 GitHub、Hacker News、Stack Exchange、Reddit、Hugging Face 等海外来源同题联查，衔接软件包与产品目录。
- **内容深。** 原帖、原图、评论、视频转写、关键帧、代码和版本信息分别读取，支持比较主张与实际实现。
- **接入灵活。** 内置只读 MCP 对接结构化来源；专用适配器和日常浏览器处理站内搜索、登录态与动态页面，B站、公众号、小红书等有具体路线。
- **视频能处理。** 已取得的媒体在本地解码、转写和抽帧，由宿主安排后台执行，再结合文字和画面产出笔记。
- **资料可复用。** 保留原始结果、来源、现有判断与未决问题，让后续追问和持续调研沿着已有材料继续。

完整的平台、内容和技术方案见[首页能力表](../README.md#能查哪些来源读哪些信息)，各入口实测日期及状态见[验收记录](verification.md)。

## 能力依据

| 宣传中的能力 | 仓库中的实现与例子 |
| --- | --- |
| 跨平台发现、核对与结论交付 | [调研入口](../skills/chinese-platform-research/SKILL.md)、[专题研究与连续调研](../skills/chinese-platform-research/references/broad-research.md) |
| 选型、选题、验证与复刻准备、查重查新 | [按目的选择调研方式](../skills/chinese-platform-research/references/use-cases.md) |
| 评论深读与来源追溯 | [21 个只读工具](../mcp/server.py)、[评论改变结论的真实案例](../examples/comments-change-the-answer.md) |
| 本地转写与关键帧材料 | [视频处理脚本](../skills/chinese-platform-research/scripts/read_video_local.py)、[视频学习流程](../skills/chinese-platform-research/references/douyin-video-learning.md) |
| 精简候选、原始结果保留 | [近期检索助手](../skills/chinese-platform-research/scripts/research_recent.py)、[回归与实测结果](verification.md) |

## 组件关系

仓库提供自己的调研 Skill、21 个只读 MCP 工具与两段本地助手脚本。近期检索助手可调用另行安装的 last30days 引擎，目前封装范围为 HN/GitHub。浏览器、B站/公众号适配器与语音模型按任务连接，见[安装说明](installation.md)。

Agent Reach 的渠道检查、OpenCLI 的浏览器复用、DyNote 的素材与笔记分离、Groundwork 的需求比较是工作流的设计参考；这些项目的整套代码未打包进本仓库。视频助手中 SRT 格式的改编保留[上游 MIT 许可](../skills/chinese-platform-research/scripts/LICENSE.video-transcriber)。
