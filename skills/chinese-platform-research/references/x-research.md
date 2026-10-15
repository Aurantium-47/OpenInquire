# X 搜索、原帖与回复

## 先区分两条路线

- **用户日常浏览器**：复用已授权的普通登录。站内搜索可用 `since:YYYY-MM-DD until:YYYY-MM-DD`、作者或关键词缩小范围，选择“最新”后核对实际日期。打开具体帖子、展开长文，再按问题读取回复和图片。搜索结果不是完整正文，回复计数也不等于已经读完全部回复；记下实际取样范围与隐藏/未加载部分。
- **`platform_research.search_x`**：需要独立的 `X_BEARER_TOKEN` 及该开发者项目的接口权限/额度。调用的是最近 7 天检索，不适合直接找多年前的帖子。`limit` 是页面大小，官方最小 10、最大 100；按返回的 `meta.next_token` 传入 `next_token` 继续读取，保持原查询不变。保留帖子 URL、作者、时间和 `conversation_id`；按会话检索回复仍受同一时间范围及可见性限制，不保证评论完整。

网页已登录不表示 API 已开通。缺少 API 凭据、额度耗尽、网页会话失效和空搜索结果是不同状态，分别记录；API 不可用时可继续使用当前已授权、正常可访问的网页。历史研究需要网页搜索或另行具备权限的全历史 API，不能把 recent search 的零结果当作历史上没人讨论。

## 开源工具选型（2026-10-15 核对）

| 项目 | 适用条件 | 本 skill 的处理 |
|---|---|---|
| [X 官方 xmcp](https://github.com/xdevplatform/xmcp) | 独立开发者凭据和端点权限；支持读写接口 | 已有官方 API 时再考虑；调研只开放需要的读取工具。不是免费数据来源，也不继承普通浏览器登录 |
| [x-browser-mcp](https://github.com/SohrabZ/x-browser-mcp) | README 支持 macOS/Linux、Chrome，使用独立配置目录 | Windows 已连接浏览器优先；不能承诺自动复用日常 Edge 登录 |
| [Xee-mcp](https://github.com/Aiyo28/Xee-mcp) | 非官方 Twikit 路线，初始化涉及 Cookie；仓库记录搜索等功能降级 | 不作为默认可用入口；先核对维护状态，不将“无需 API”写成已验收 |

已有浏览器能完成读取时，无需另装一套登录系统。普通登录按用户现有授权处理；个人授权与本机账号细节保留在本机，不写入公共发布版本。

## 验收与来源

最小验收：搜索返回相关内容 → 打开一篇原帖 → 读取可见回复并记录未读部分。图片、视频另按媒体流程读取，不能由正文替代。API 缺凭据时只验收缺凭据返回和浏览器路线，不声称 API 联网查询成功。

官方检索范围与分页：[Recent search quickstart](https://docs.x.com/x-api/posts/search/quickstart/recent-search)；[官方文档源码](https://github.com/xdevplatform/docs/blob/main/x-api/posts/search/quickstart/recent-search.mdx)。API 的费用、权限和返回字段以实际调用时的文档及响应为准。
