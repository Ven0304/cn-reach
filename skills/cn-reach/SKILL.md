---
name: cn-reach
description: >
  Read-only access to Chinese platforms that built-in web search and fetch cannot reach:
  WeChat Official Account articles (微信公众号: read a link, search by keyword), Bilibili (B站: search,
  video info, subtitles), Xiaohongshu (小红书: search notes, read, comments), Xueqiu (雪球: quotes, hot posts),
  V2EX, and Xiaoyuzhou podcast transcripts. Use when the user shares a link from mp.weixin.qq.com,
  bilibili.com, b23.tv, xiaohongshu.com, xhslink.com, xueqiu.com, v2ex.com or xiaoyuzhoufm.com; asks to
  search or read on one of these platforms by name; or wants subtitles for a Bilibili or YouTube video.
  For general web research, news, English-language sites and GitHub, use the built-in tools instead.
---

# cn-reach

Two tools, one output format:
- `scripts/wechat.py` in this skill's directory, for WeChat. Python 3 standard library only.
- The `agent-reach` CLI (version 1.6 or later), for the other platforms.

## Routing

- A general question on a topic, Chinese or not, goes to WebSearch / WebFetch. This skill is for the cases listed in the description.
- When the user names a platform above or shares one of its links, call the matching command directly. It returns fuller content (article bodies, replies, subtitles) than WebFetch does on these sites.
- Run only the command the request needs. Use `agent-reach channels`, `doctor` or `check` when a command fails or an action's parameters are unclear.

## WeChat Official Accounts

`<skill-dir>` is the base directory shown when this skill loads. Use `python` on Windows, `python3` elsewhere.

```bash
python "<skill-dir>/scripts/wechat.py" read "https://mp.weixin.qq.com/s/..."           # one article
python "<skill-dir>/scripts/wechat.py" read "<link>" --max-chars 8000                   # cap long articles
python "<skill-dir>/scripts/wechat.py" search "关键词" --limit 5                         # title, account, date, snippet
python "<skill-dir>/scripts/wechat.py" search "关键词" --limit 5 --resolve               # also returns mp.weixin.qq.com links
```

- Search goes through Sogou Weixin and is ranked by relevance, so results can be years old. Check `published_at`, and when the user wants recent coverage, point out which results are old.
- Search returns snippets only. To give the user article content, resolve and read the one to three most relevant results.
- Resolved links carry a signature that expires. They are fine as citations; mention that they are temporary.
- `[image N]` in the text marks the Nth entry of `images`. Image content is not available; describe only the text.

## Other platforms (agent-reach)

Form: `agent-reach <channel> <action> <required args> [--optional value]`, or `agent-reach read <link>` to pick the channel from the URL.

| Platform | Commands | Notes |
|---|---|---|
| Bilibili | `bilibili search "关键词" --limit 5`, `bilibili read <BV id or link>`, `bilibili subtitle <BV id or link>`, `bilibili hot` | Subtitles need a one-time QR login |
| Xiaohongshu | `xiaohongshu search "关键词" --limit 5`, `xiaohongshu read <full link with xsec_token>`, `xiaohongshu comments <same>` | Optional channel; needs a login. `read` returns text only |
| Xueqiu | `xueqiu quote SH600519`, `xueqiu search "茅台"`, `xueqiu hot_posts`, `xueqiu hot_stocks` | Quotes work without a login |
| V2EX | `v2ex hot`, `v2ex node python`, `v2ex read <link or id>` | |
| YouTube | `youtube subtitle <link>` | For subtitles; other YouTube questions go to the built-in tools |
| Xiaoyuzhou | `xiaoyuzhou transcribe <episode link>` | Uses the user's Groq quota and can take up to 15 minutes; confirm with the user first |

## Results and errors

Both tools print one line of JSON.

- `ok: true`: content is in `items`; each item has `title / url / author / published_at / text`.
- `ok: false`: act on `error.code`, using `error.hint`:

| code | Action |
|---|---|
| `NEED_SETUP` | The channel is not installed. Suggest `/cn-reach:setup`, or run `agent-reach add <channel>` once the user agrees |
| `NEED_LOGIN` | Deliver what was already retrieved, then tell the user a login is needed. `agent-reach login <channel>` opens a window where the user signs in |
| `PLATFORM_BLOCKED`, `RATE_LIMITED` | The platform wants a verification check or is throttling. Stop and tell the user |
| `TIMEOUT`, `UPSTREAM_BROKEN` | Retry once. If it fails again, tell the user which platform is unavailable and fall back to the built-in tools |
| `NOT_FOUND` | The content was deleted or moved, or the link is wrong |
| `BAD_INPUT` | Wrong arguments; `agent-reach channels` lists the usage |

If `agent-reach` is not found, or prints a plain `Agent Reach v1.5.x` line instead of JSON, it is missing or too old: suggest `/cn-reach:setup`. The WeChat script works without it.

## Scope

- Read only: search and read; no posting, commenting, liking or messaging.
- The user signs in themselves. Credentials, cookies and keys are never requested or printed.
- Installing, upgrading and configuring happen in `/cn-reach:setup` or when the user asks.
