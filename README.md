# cn-reach

English | [中文](README.zh-CN.md)

A Claude Code plugin for read-only access to Chinese platforms that built-in web search and fetch cannot reach. An independent project built on the [agent-reach](https://github.com/Panniantong/Agent-Reach) CLI.

| Platform | What it does | Backend |
|---|---|---|
| WeChat Official Accounts | Read an article link; search articles by keyword | Bundled `scripts/wechat.py` (standard library; search via Sogou Weixin) |
| Bilibili | Search, video info, subtitles, trending | agent-reach CLI 1.6+ |
| Xiaohongshu | Search notes, read, comments (login required) | agent-reach |
| Xueqiu | Quotes, stock search, hot posts, hot stocks | agent-reach |
| V2EX, YouTube subtitles, Xiaoyuzhou | See `skills/cn-reach/SKILL.md` | agent-reach |

The skill is used when a request names one of these platforms, includes one of their links, or asks for video subtitles. Other web questions go to Claude's built-in tools. Setup and upgrades run through `/cn-reach:setup`.

## Install

Either way, then start a new session and run `/cn-reach:setup` to install or upgrade agent-reach and check each channel.

**Claude desktop app:** download `cn-reach.zip` from the [latest release](https://github.com/Ven0304/cn-reach/releases/latest), then open **Customize → Plugins → Add → Upload plugin** and choose it.

**Claude Code CLI:**

```
/plugin marketplace add Ven0304/cn-reach
/plugin install cn-reach@cn-reach-marketplace
```

## Limitations

- Sogou Weixin ranks by relevance, not date, and asks for a captcha under frequent use.
- `mp.weixin.qq.com` links resolved from search results are signed and expire.
- Read only: no posting, commenting or signing in on the user's behalf.

## Disclaimer

For personal study and research. Requests are made one at a time at the user's prompt; the plugin stops when a platform asks for verification and does not bypass captchas or rate limits. Users are responsible for complying with each platform's terms of service and applicable law. Do not use it for bulk collection, commercial data harvesting, or collecting personal information.

## Layout

```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   marketplace entry
skills/cn-reach/SKILL.md          routing, commands, error handling
skills/cn-reach/scripts/wechat.py WeChat read and search
skills/setup/SKILL.md             /cn-reach:setup (runs only when the user types it)
```

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

- [agent-reach](https://github.com/Panniantong/Agent-Reach) (MIT) for every non-WeChat channel; installed separately, not bundled.
- The Sogou Weixin search approach follows [weixin_search_mcp](https://github.com/fancyboi999/weixin_search_mcp) (MIT).
