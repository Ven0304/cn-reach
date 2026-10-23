#!/usr/bin/env python3
"""WeChat Official Account articles: read a link, or search by keyword via Sogou Weixin.

Standard library only. Prints one line of JSON.

    python wechat.py read <mp.weixin.qq.com link> [--max-chars N]
    python wechat.py search <keywords> [--limit N] [--page N] [--resolve]

Output shape (same as agent-reach):
    {"ok": true, "items": [{title, url, author, published_at, text, ...}]}
    {"ok": false, "error": {"code": ..., "message": ..., "hint": ...}}
"""
import argparse
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
TIMEOUT = 15
CST = timezone(timedelta(hours=8))


class ReachError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.message, self.hint = code, message, hint


def _opener():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [
        ("User-Agent", UA),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.6"),
    ]
    return op


def _get(op, url, referer=None):
    req = urllib.request.Request(url)
    if referer:
        req.add_header("Referer", referer)
    try:
        with op.open(req, timeout=TIMEOUT) as resp:
            return resp.geturl(), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise ReachError("UPSTREAM_BROKEN", f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise ReachError("TIMEOUT", f"Request failed: {getattr(e, 'reason', e)}", "Check the network and try once more")


def _ts(value):
    try:
        return datetime.fromtimestamp(int(value), CST).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _strip_tags(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


# ── read ──

class _ContentParser(HTMLParser):
    """Turn #js_content into plain text with paragraph breaks and image placeholders."""

    BLOCK = {"p", "div", "section", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "tr"}
    SKIP = {"script", "style"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0      # nesting depth inside js_content; 0 means outside the article body
        self.skip = 0
        self.parts = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth == 0:
            if a.get("id") == "js_content":
                self.depth = 1
            return
        if tag not in self.VOID:
            self.depth += 1
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "img":
            src = a.get("data-src") or a.get("src")
            if src and src.startswith("http"):
                self.images.append(src)
                self.parts.append(f"\n[image {len(self.images)}]\n")
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        # <br/>, <img/>: a start tag only; <div/> and friends: open and close.
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.depth == 0 or tag in self.VOID:
            return
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        self.depth -= 1

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.parts.append(data)

    def text(self):
        raw = "".join(self.parts).replace("\xa0", " ")
        lines = [ln.strip() for ln in raw.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _js_var(page, name):
    m = re.search(rf"var\s+{name}\s*=\s*(?:htmlDecode\()?\s*[\"']([^\"']*)[\"']", page)
    return html.unescape(m.group(1)).strip() if m else None


def _meta(page, prop):
    m = re.search(rf'<meta[^>]+property="{prop}"[^>]+content="([^"]*)"', page)
    return html.unescape(m.group(1)).strip() if m else None


# Page text WeChat shows instead of an article, mapped to an English message.
_GONE = {
    "该内容已被发布者删除": "Deleted by the publisher",
    "此内容因违规无法查看": "Removed for violating platform rules",
    "该公众号已迁移": "The account has migrated",
    "内容已删除": "Deleted",
    "链接已过期": "The link has expired",
    "参数错误": "Invalid article link",
}


def read_article(url, max_chars=None, op=None, referer=None):
    if not re.match(r"https?://mp\.weixin\.qq\.com/", url):
        raise ReachError("BAD_INPUT", "Not a WeChat article link", "Expected https://mp.weixin.qq.com/s/...")
    op = op or _opener()
    final_url, page = _get(op, url, referer)

    if "环境异常" in page or "完成验证后即可继续访问" in page or "wappoc_appmsgcaptcha" in final_url:
        raise ReachError("PLATFORM_BLOCKED", "WeChat is asking for a verification check",
                         "Ask the user to open the article in a browser and complete the check")
    if 'id="js_content"' not in page:
        for marker, message in _GONE.items():
            if marker in page:
                raise ReachError("NOT_FOUND", message)
        raise ReachError("UPSTREAM_BROKEN", "No article body on the page (video, image post, or a layout change)",
                         "Suggest opening it in a browser, or try the built-in web reader once")

    parser = _ContentParser()
    parser.feed(page)
    text = parser.text()
    truncated = False
    if max_chars and len(text) > max_chars:
        text, truncated = text[:max_chars], True

    title = _meta(page, "og:title") or _js_var(page, "msg_title")
    author = _js_var(page, "nickname")
    if not author:
        m = re.search(r'id="js_name"[^>]*>(.*?)</', page, re.S)
        author = _strip_tags(m.group(1)) if m else None
    m = re.search(r'var\s+ct\s*=\s*"(\d+)"', page)
    return {
        "title": title,
        "url": url,
        "author": author,
        "published_at": _ts(m.group(1)) if m else None,
        "text": text,
        "truncated": truncated,
        "images": parser.images,
        "summary": _meta(page, "og:description"),
    }


# ── search (Sogou Weixin) ──

_ANTISPIDER = ("antispider", "seccodeRight", "anti.min.css", "请输入验证码")


def _resolve_sogou_link(op, link, referer):
    """Sogou's redirect page assembles the real link in pieces: url += '...'."""
    final_url, page = _get(op, link, referer)
    if any(k in final_url or k in page for k in _ANTISPIDER):
        raise ReachError("PLATFORM_BLOCKED", "Sogou is asking for a captcha")
    if final_url.startswith("https://mp.weixin.qq.com/"):
        return final_url
    parts = re.findall(r"url \+= '([^']*)'", page)
    real = "".join(parts).replace("@", "")
    if not real:
        return None
    return real if real.startswith("http") else "https://mp." + real


def search(query, limit=5, page=1, resolve=False):
    op = _opener()
    _get(op, "https://weixin.sogou.com/")  # picks up the session cookies Sogou expects
    params = urllib.parse.urlencode({"type": 2, "s_from": "input", "query": query, "ie": "utf8", "page": page})
    search_url = f"https://weixin.sogou.com/weixin?{params}"
    final_url, body = _get(op, search_url, "https://weixin.sogou.com/")
    if any(k in final_url or k in body for k in _ANTISPIDER):
        raise ReachError("PLATFORM_BLOCKED", "Sogou is asking for a captcha",
                         "Try again later, or ask the user to complete the check at weixin.sogou.com")

    items = []
    for block in re.findall(r'<li id="sogou_vr_11002601_box_\d+".*?</li>', body, re.S)[:limit]:
        a = re.search(r'<h3>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not a:
            continue
        link = urllib.parse.quote(html.unescape(a.group(1)), safe="/?&=%:._-~+")
        if link.startswith("/"):
            link = "https://weixin.sogou.com" + link
        summary = re.search(r'<p class="txt-info"[^>]*>(.*?)</p>', block, re.S)
        account = re.search(r'<span class="all-time-y2">(.*?)</span>', block, re.S)
        ts = re.search(r"timeConvert\('(\d+)'\)", block)
        items.append({
            "title": _strip_tags(a.group(2)),
            "url": link,
            "author": _strip_tags(account.group(1)) if account else None,
            "published_at": _ts(ts.group(1)) if ts else None,
            "text": _strip_tags(summary.group(1)) if summary else "",
        })

    if resolve:
        for i, item in enumerate(items):
            if i:
                time.sleep(1)  # Sogou throttles rapid redirects
            try:
                real = _resolve_sogou_link(op, item["url"], search_url)
            except ReachError as e:
                if e.code == "PLATFORM_BLOCKED":
                    break  # the rest would fail too; keep what we have
                raise
            if real:
                item["sogou_url"], item["url"] = item["url"], real
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wechat.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read", help="read one article")
    r.add_argument("url")
    r.add_argument("--max-chars", type=int, default=None)
    s = sub.add_parser("search", help="search articles by keyword (Sogou Weixin)")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--page", type=int, default=1)
    s.add_argument("--resolve", action="store_true", help="replace Sogou redirect links with mp.weixin.qq.com links (slower)")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "read":
            items = [read_article(args.url, args.max_chars)]
        else:
            items = search(args.query, max(1, min(args.limit, 10)), args.page, args.resolve)
        out = {"ok": True, "channel": "wechat", "action": args.cmd, "items": items}
    except ReachError as e:
        out = {"ok": False, "channel": "wechat", "action": args.cmd,
               "error": {"code": e.code, "message": e.message, "hint": e.hint}}
    except Exception as e:  # unexpected page changes still produce the JSON contract
        out = {"ok": False, "channel": "wechat", "action": args.cmd,
               "error": {"code": "UPSTREAM_BROKEN", "message": f"{type(e).__name__}: {e}",
                         "hint": "The page layout may have changed; report WeChat as unavailable for now"}}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
