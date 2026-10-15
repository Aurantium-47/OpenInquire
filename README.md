# OpenInquire

**让 Agent 用上抖音、小红书、B站和公众号里的资料。**

跨中外平台的多模态调研 Skill · 21 个只读 MCP 工具 · 登录态浏览器 · 本地视频处理

OpenInquire 为这四个平台提供专门的搜索与读取流程：复用日常浏览器的登录状态，连接平台适配器提取图文和字幕，再把已取得的视频转成带时间点的文字与关键帧。经验帖、评论补充、视频教程和公众号长文，都有对应的处理方式。

[开始使用](docs/installation.md) · [与同类工具对比](docs/comparison.md) · [真实案例](examples/comments-change-the-answer.md) · [近期实测](docs/verification.md)

## 难接入的平台，我们怎么读

**针对登录、动态页面和视频内容，按平台选择读取方式。** 浏览器负责站内搜索和页面读取，专用 MCP 与适配器负责内容提取，本地脚本负责视频转写和抽帧。Agent 再将取得的材料读完、核对，整理成有出处的结论。

| 平台或材料 | 我们采用的方案 | 解决的具体问题 |
| --- | --- | --- |
| 抖音与本地视频 | 浏览器核对作品 ID，取得页面提供的媒体；FFmpeg 解码、离线 ASR、定时与场景变化抽帧 | 将口播和画面变成可查阅、带时间点的材料，后台处理时可继续其他工作 |
| 小红书、知乎 | 在用户已连接的日常浏览器中搜索，读取页面 DOM、原图与展开的评论 | 复用现有登录态，读取站内原帖、具体回答和动态加载的内容 |
| B站 | 连接 `bilibili_mcp`、`bili-note` 或正常网页，按任务读取搜索结果、图文、字幕和评论 | 为视频发现、内容提取与学习笔记选择合适工具，保留来源与素材 |
| 微信公众号 | 用 `wechat_public` 发现文章，公开直链通过文章适配器或正常网页提取正文、图片和元数据 | 将搜索线索继续追到可正常访问的文章原文，并核对图文是否完整 |
| 海外社区与开源生态 | REST/JSON/Atom/GraphQL 等来源封装为只读 MCP，按权限与任务选择 | 直接检索帖子、仓库、评论、版本与依赖信息，再按需深读原始内容 |

历史样本已完成公众号正文与图片导出、抖音视频转写与抽帧。浏览器和平台适配器按[安装说明](docs/installation.md)连接；各平台当前可读到哪一层、哪些环节仍受限制，见[实测记录](docs/verification.md)。具体做法见[中文平台](skills/chinese-platform-research/references/local-channels.md)、[公众号](skills/chinese-platform-research/references/wechat-articles.md)、[视频学习](skills/chinese-platform-research/references/douyin-video-learning.md)和[技术平台](skills/chinese-platform-research/references/tech-platforms.md)。

在小红书、知乎、公众号里找实践经验，在 Reddit、Hacker News、Stack Exchange 里找讨论与反例，再到 GitHub、Hugging Face 和视频平台核对实现。OpenInquire 把这些来源放进同一轮调研：评论有没有推翻原帖？视频里的方法能否复刻？已有项目做到哪一步，自己的想法还剩多少新东西？

**把来回搜、翻、看、比较的工作交给 OpenInquire，把精力用在选题、验证和创造上。**

## 为什么选择 OpenInquire

- **抖音、小红书、B站、公众号有专门的读取流程。** 把登录态浏览器、平台适配器、正文提取和视频处理组合起来，让 Agent 按内容类型选择工具，继续读取站内材料。
- **覆盖广：国内经验与海外一手资料一起查。** 中文内容平台、海外社区、代码仓库、模型与数据集、软件包和产品目录都有对应入口；按问题选来源，跨语言核对同一件事。
- **读得深：正文、图片、评论、字幕、视频画面和代码都能成为材料。** 跟进作者更正、楼中讨论、教程步骤和实现细节，让关键结论有原文、评论链接或时间点可查。
- **视频能在后台处理。** 已取得的媒体交给 FFmpeg 与离线 faster-whisper，生成带时码转写、字幕、关键帧和联系表；Agent 再结合文字与画面整理教程、案例和学习笔记。
- **已有资料可以接着用。** 精简候选先供 Agent 筛选，完整结果和日志留在本地；已读来源、素材和未决问题可以复用，换问题、补证据、做长专题时少从头再查。

## 与同类工具对比

| 你熟悉的工具 | 它主打的环节 | OpenInquire 接着帮你完成 |
| --- | --- | --- |
| [Agent Reach](https://github.com/Panniantong/Agent-Reach) | 配好渠道，让 Agent 能访问互联网 | 选哪些来源、追哪些评论、如何核对冲突说法，再交付主题结论与来源 |
| [OpenCLI](https://github.com/jackwener/OpenCLI) | 把网站变成可调用的命令，复用已登录浏览器 | 围绕研究问题安排跨站搜索、深读、比较和整理，产出可以继续使用的调研材料 |
| [last30days](https://github.com/mvanhorn/last30days-skill) | 从 Reddit、X、YouTube 等来源发现近期讨论并综合 | 补入小红书、知乎、公众号等中文站内经验，把近期线索与历史原文、视频过程及代码实现一起核对 |
| [DyNote](https://github.com/Rimagination/dy-note) | 深入抖音视频、评论、账号与话题，形成学习资产 | 将视频中的观点带到其他平台求证，再对照文章、开发者讨论和公开实现 |
| [Groundwork](https://github.com/SC-Airu/groundwork-skill) | 开工前扫描问题、现有方案和需求缺口 | 深入中文平台原帖与多模态材料，保留已读来源，让专题研究可以持续推进 |

**跨平台发现、原帖与评论深读、视频理解、来源核对、结论交付——在一个调研入口里完成。** [详细对比与能力依据](docs/comparison.md)

## 适用场景

| 你想做的事 | OpenInquire 帮你查清什么 | 你带走什么 |
| --- | --- | --- |
| **少造重复的轮子** | 已有开源项目、成熟组件、实际使用反馈和接入条件 | 可复用方案、选型比较、需要自己补的部分 |
| **找到值得做的选题** | 人们反复遇到的问题、现有方案的不足、不同场景的需求 | 有材料依据的选题方向与可检验的问题 |
| **验证想法，准备复刻** | 相似案例、实现步骤、环境版本、数据与效果证据 | 最小验证方案、复刻路线和关键依赖 |
| **查重查新** | 最接近的论文、项目、产品与历史讨论 | 已有工作对照、具体差异、检索范围和待验证点 |
| **学透教程和案例** | 视频过程、关键画面、字幕与评论补充 | 带时码的学习笔记和可复用素材 |
| **做选题写作与趋势研究** | 近期变化、不同群体的观点、原始出处与反例 | 有来源的素材包、观点比较与后续线索 |

学术选题与查新会进一步跟进论文、官方文档及公开实现；复刻路线会明确输入、环境与验证标准。[各类任务的使用方式](skills/chinese-platform-research/references/use-cases.md)

## 可以直接这样提问

> 我想做【项目】。先找已有实现和使用反馈，比较哪些能直接复用，哪些地方值得自己做。

> 这是我的想法【描述】。查最接近的论文、开源项目和产品，标出相同点、真正的差异，以及怎样用一个小实验验证。

> 最近大家怎么用 AI 学习视频？一起查小红书、B站、Reddit、Hacker News 和 GitHub，比较实际效果、成本和使用条件。

> 研究这个选题。看看小红书、知乎、公众号上分别怎么讨论，找出共识、分歧和容易被忽略的细节。

> 把这组已取得的视频学透：整理步骤、关键画面和时间点，再结合评论里的补充，做成以后能回看的笔记。

> 接着上次的调研，补查没解决的问题，告诉我哪些新材料改变了原来的判断。

## 能查哪些来源，读哪些信息

| 来源 | 平台与内容 | 接入方式 |
| --- | --- | --- |
| 中文经验与长文 | 小红书原帖/图片、知乎回答/文章、公众号图文，以及可展开的讨论 | 日常登录态浏览器、公众号文章适配器 |
| 视频与教程 | 抖音、B站的作品与学习材料；YouTube 视频候选 | 浏览器及 B站专用工具；YouTube MCP 检索；已取得媒体再做字幕/ASR与画面读取 |
| 技术问答与社区 | Hacker News、Stack Exchange、V2EX 的问答/讨论/评论；Lobsters 的话题线索 | 内置只读 MCP；需要原文时继续跟进来源 |
| 海外社交与产品 | Reddit、Bluesky、Mastodon、X、Product Hunt 的帖子、动态和产品线索 | 公开 API、Atom 或已授权 API；[X 浏览器与 API 路线](skills/chinese-platform-research/references/x-research.md)分开验收 |
| 开源项目与实现 | GitHub 仓库、Issue/PR 评论与审查回复；GitLab、Gitee 项目 | 内置只读 MCP 发现与读讨论，代码和文档继续回到原仓库核对 |
| 模型、数据和依赖 | Hugging Face 模型/数据集/Spaces；npm、PyPI、crates.io、Docker Hub 的版本与元数据 | 内置只读 MCP；模型卡和实现按任务进一步读取 |

[具体工具与前提](skills/chinese-platform-research/references/tech-platforms.md) · [中文平台路线](skills/chinese-platform-research/references/local-channels.md)

## 调研开始前，先确认这条路今天能走

每条渠道分别记录搜索、正文、评论和媒体的实测状态。运行时先用小样本确认当前入口，再扩大调研；某一来源暂时失效，已取得的材料保留，其他相关来源继续。

最近一轮增量验收：**2026-10-15**，X 网页搜索、原帖和一条回复可读，API 分页回归与 21 个只读工具列出通过；API 凭据未配置。此前已验证技术社区的五类评论样本、本地视频转写及抽帧。各平台按实际测试日期记录可读层级。[查看实测范围](docs/verification.md)

## 一个真实例子：后续回复改变了结论

在调研 Agent Reach 的配置说明时，我们读到一个环境问题报告。作者先在回复里将原因归于本地拷贝，后来又更正判断、补上上游修复提交。继续打开代码，才能核实究竟改了什么。这个过程用本仓库的评论工具读到了三条回复，并核对了原始 diff。[查看案例与来源](examples/comments-change-the-answer.md)

同样的方法可以用来判断一篇经验帖的适用条件、一条视频教程的后续补充，或一个开源方案的实际状态。

## 轻量组合，按需接入

```mermaid
flowchart LR
    Q[你的问题] --> S[调研 Skill]
    S --> W[中外平台与日常浏览器]
    S --> M[社区与开源生态只读 MCP]
    S --> V[本地字幕与视频处理]
    W --> E[原帖 · 评论 · 画面 · 代码]
    M --> E
    V --> E
    E --> R[综合判断与来源笔记]
```

仓库提供调研 Skill、**21 个只读 MCP 工具**和本地处理脚本。浏览器、站点适配器、可选近期检索引擎与语音模型按任务接入，现有工具可以继续使用。[组件与安装说明](docs/installation.md)

当前验收环境为 Windows + Codex。各平台的正文、评论和媒体可用范围单独记录，便于选用合适路线。[查看最新验收](docs/verification.md)

安装到用户级 Skill 目录后，可以在不同项目中调用：

```text
用 $chinese-platform-research 调研【主题】。
关注【时间范围和重点】，先给主要判断，再附能回查的来源。
```

`chinese-platform-research` 是保留兼容的调用名；平台和语言范围按调研问题选择，国内与海外来源均可使用。

## 开源致谢

感谢 [Agent Reach](https://github.com/Panniantong/Agent-Reach)、[OpenCLI](https://github.com/jackwener/OpenCLI)、[last30days](https://github.com/mvanhorn/last30days-skill)、[DyNote](https://github.com/Rimagination/dy-note) 和 [Groundwork](https://github.com/SC-Airu/groundwork-skill) 对渠道检查、浏览器复用、近期发现、视频资产与需求研究的探索。设计参考、可选依赖和代码改编分别记录在[组件关系](docs/comparison.md#组件关系)中。

原创代码与文档采用 [MIT](LICENSE)。视频助手中的 SRT 格式改编保留了 [上游 MIT 许可](skills/chinese-platform-research/scripts/LICENSE.video-transcriber)。其余独立工具按各自许可证安装。
