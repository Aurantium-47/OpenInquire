# 安装与配置


按任务选择组件：先安装 Skill，再连接需要的浏览器、MCP 或视频处理环境。

| 组件 | 包含在本仓库 | 前提 |
| --- | --- | --- |
| 调研Skill、两段本地助手脚本 | 是 | 支持Skill的宿主；Python3.12已验收 |
| 技术社区只读MCP（21工具） | 是 | Python3.12与 `mcp/requirements.txt` |
| 日常浏览器读取中文平台 | 否 | 宿主支持的浏览器扩展、相应站点正常登录 |
| B站/公众号专用适配器 | 否 | 单独安装和验证，见渠道文档 |
| last30days候选引擎 | 否，可选 | 独立安装的上游代码；封装只启用HN/GitHub |
| 视频本地处理 | 助手脚本是 | FFmpeg/FFprobe、Pillow；转写另需faster-whisper和完整本地模型 |

将 `skills/chinese-platform-research` 目录安装到宿主用户级skills目录。例如Codex常用 `$CODEX_HOME/skills`，未自定义时为用户目录下 `.codex/skills`。同名已存在时先比较并合并，避免覆盖个人更新。

在仓库根目录为可选MCP创建独立环境：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r mcp/requirements.txt
.\.venv\Scripts\python.exe mcp/server.py
```

macOS/Linux用 `python3.12`、`.venv/bin/python` 对应替换；本轮未实测这些系统。服务使用stdio，不监听公开端口。将宿主MCP配置中的command设为该虚拟环境Python绝对路径，args设为 `server.py` 绝对路径。不要照抄别人的个人目录，也不覆盖现有MCP配置。

```json
{
  "command": "<绝对路径>/.venv/Scripts/python.exe",
  "args": ["<绝对路径>/mcp/server.py"]
}
```

这是通用stdio字段示例；外层配置格式以当前宿主为准。连接后先列工具，再运行小样本，`platform_access_status`只检查配置，不是联网验收。

视频依赖按需要安装在所用Python环境：

```powershell
py -3.12 -m pip install Pillow faster-whisper
py -3.12 skills/chinese-platform-research/scripts/read_video_local.py '<媒体路径>' --out '<全新输出目录>' --model '<完整本地模型目录>' --source-url '<原作网址>'
```

FFmpeg/FFprobe需在PATH中。模型须为faster-whisper可用目录；脚本不自动下载模型。已有字幕或无音轨视频用 `--no-asr`，仅处理音频可用 `--no-frames`。
