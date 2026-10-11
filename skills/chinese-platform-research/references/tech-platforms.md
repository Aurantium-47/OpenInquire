# 技术社区与开源生态

可选只读MCP源码在本仓库 `mcp/server.py`，安装前提见仓库README。服务端定义21个工具；连接后列出实际可见工具，不能以源码有函数推定当前会话已加载。

| 问题 | 入口 | 边界 |
| --- | --- | --- |
| 项目、issue、版本反馈 | `search_github`、`get_github_comments` | 普通讨论与PR行审查分开；不是Discussions接口 |
| 社区讨论与反例 | `search_hacker_news`、`get_hacker_news_thread`、`get_lobsters_feed` | HN依赖Algolia索引，删除/未索引内容可能缺失 |
| 可复现技术问答 | `search_stack_exchange`、`get_stack_exchange_thread` | 区分题面、答案和评论，遵守backoff |
| 中文开发者讨论 | `get_v2ex_feed`、`get_v2ex_topic`；Linux.do正常浏览器 | `linux_do_search_route`只给入口，不实际读帖子 |
| 模型、数据集、依赖 | `search_hugging_face`、`search_packages`、`get_pypi_package`、`search_code_hosts` | 搜索元数据不等于已读模型卡/代码；GitLab/Gitee、npm/crates/Docker按参数选择 |
| 视频发现 | `search_youtube` | API Key可选，无Key需独立yt-dlp；仅返回候选，不等于字幕已读 |
| 更多公开社区 | `search_bluesky`、`get_mastodon_public`、`search_reddit` | Mastodon因实例不同；Reddit Atom可含社区链接，确认具体帖子 |
| 新产品 | `get_product_hunt_posts` | 无Token用公开Atom；推广主张需外部核对 |
| X动态 | `search_x` | 官方API需单独凭据；网页登录不等于API权限 |

`platform_access_status`只展示配置与可选凭据是否存在，不打印秘密，也不做联网可用性保证。凭据缺失时保留相应渠道缺口；有授权且可访问的正常浏览器可独立完成网页任务。

技术事实用官方文档、源代码、论文或原作者材料验证；社区用于发现实践、反例和争议，不用点赞量证明正确性。
