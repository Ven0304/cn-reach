# cn-reach

[English](README.md) | 中文

一个 Claude Code 插件，让 Claude 能只读访问自带网页搜索和读取够不着的中文平台。这是基于 [agent-reach](https://github.com/Panniantong/Agent-Reach) 命令行工具的独立项目。

| 平台 | 能做什么 | 底层 |
|---|---|---|
| 微信公众号 | 读文章链接；按关键词搜文章 | 自带脚本 `scripts/wechat.py`（只用标准库；搜索走搜狗微信） |
| B站 | 搜索、视频信息、字幕、热门 | agent-reach CLI 1.6+ |
| 小红书 | 搜笔记、读正文、看评论（需登录） | agent-reach |
| 雪球 | 行情、搜股票、热帖、热股 | agent-reach |
| V2EX、YouTube 字幕、小宇宙 | 见 `skills/cn-reach/SKILL.md` | agent-reach |

只有在请求里点名这些平台、贴出它们的链接，或者要视频字幕时，才会用到这个插件；其他网页问题仍由 Claude 自带工具处理。安装和升级通过 `/cn-reach:setup` 进行。

## 安装

用下面任一方式装好后，开一个新会话，运行 `/cn-reach:setup`，它会安装或升级 agent-reach，并检查各个平台。

**Claude 桌面应用**：从[最新 Release](https://github.com/Ven0304/cn-reach/releases/latest) 下载 `cn-reach.zip`，然后打开 **Customize → Plugins → Add → Upload plugin** 选择它。

**Claude Code 命令行**：

```
/plugin marketplace add Ven0304/cn-reach
/plugin install cn-reach@cn-reach-marketplace
```

## 使用

不用记命令，直接用中文说想要什么，例如：

- "读一下这篇：https://mp.weixin.qq.com/s/..."
- "公众号上搜一下人形机器人丝杠最近的文章"
- "B站上搜一下减速器拆解的视频"
- "雪球查一下 SH600519 的行情"

需要登录的功能（B站字幕、小红书正文、雪球热帖等），在自己的终端里运行 `agent-reach login <平台>`，在弹出的窗口里登录一次即可。

## 已知限制

- 搜狗微信按相关度排序，不按时间；频繁请求会触发验证码。
- 从搜索结果还原出的 `mp.weixin.qq.com` 链接带签名，过一段时间会失效。
- 只读：不发帖、不评论，也不代用户登录。

## 免责声明

仅供个人学习和研究使用。每次请求都由用户发起、逐条进行；平台要求验证时插件会停下，不绕过验证码或限流。使用者需自行遵守各平台的用户协议和适用法律。请勿用于批量采集、商业数据抓取或收集个人信息。

## 目录结构

```
.claude-plugin/plugin.json        插件清单
.claude-plugin/marketplace.json   插件市场条目
skills/cn-reach/SKILL.md          选路、命令、错误处理
skills/cn-reach/scripts/wechat.py 公众号读取和搜索
skills/setup/SKILL.md             /cn-reach:setup（只在用户手动输入时运行）
```

## 许可

MIT，见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

- [agent-reach](https://github.com/Panniantong/Agent-Reach)（MIT）：提供除公众号以外的所有渠道；需单独安装，未打包在本项目中。
- 搜狗微信搜索的思路参考了 [weixin_search_mcp](https://github.com/fancyboi999/weixin_search_mcp)（MIT）。
