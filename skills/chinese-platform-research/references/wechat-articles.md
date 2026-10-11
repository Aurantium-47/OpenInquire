# 公众号文章

本仓库不附带微信登录、代理或第三方公众号服务。当前工具明确拒绝的读取，不能通过换MCP、镜像或代理继续；下面仅描述正常可访问且获准的渠道。

- 无直链：已安装的 `wechat_public/search_public_articles` 可以发现候选，摘要不当正文。
- 有公开直链：单独安装并审查 [odyecho/mcp-server-wechat](https://github.com/odyecho/mcp-server-wechat) 后，按该版本schema调用 `get_public_article_content`。历史版本参数使用 `input.article_url`、`format=json`、`detail=detailed`、`extract_images=true`。
- 需要导出图文：可另评估 [WxArticleSaver](https://github.com/shanliuling/WxArticleSaver)。它可能涉及本机证书、代理和微信重启；按当前任务授权及宿主规则处理，不把安装本Skill等同于授予这些权限。

验收正文须检查URL、标题、有效正文、图片及缺失资源。验证码/安全检查页即使HTTP200也算失败。长短链接有版本差异，不擅自删改签名参数；避免搜狗跳转失败后循环重试。

归档时检查文本、元数据、图片实际下载数；发现视频不等于下载成功。代理操作如确已授权，保留原状态并在完成或失败后恢复，报告遗留证书；绝不把代理、凭据或原作者的机器配置打包发布。

历史开发环境曾验证一篇文章正文和图文导出；这不保证当前环境、任意文章或全平台可用。当前任务仍需逐次检查。
