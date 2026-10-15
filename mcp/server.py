"""Read-only MCP adapters for public technology-research sources."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


mcp = FastMCP("platform-research")
USER_AGENT = "Codex-Platform-Research/1.0"
TIMEOUT = 25.0
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)
# Request URLs can contain API keys (for example YouTube's key parameter).
logging.getLogger("httpx").setLevel(logging.WARNING)


def _get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=request_headers) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _post_json(url: str, *, data: dict[str, str] | None = None, json_body: Any = None, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=request_headers) as client:
        response = client.post(url, data=data, json=json_body)
        response.raise_for_status()
        return response.json()


def _get_text(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> str:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/atom+xml, application/rss+xml, text/xml"}
    if headers:
        request_headers.update(headers)
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=request_headers) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.text


def _atom_items(xml_text: str, limit: int) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    items = []
    for entry in root.findall("atom:entry", namespace)[:_limit(limit)]:
        link = next((node.get("href") for node in entry.findall("atom:link", namespace) if node.get("rel", "alternate") == "alternate"), None)
        author = entry.find("atom:author/atom:name", namespace)
        items.append({
            "title": entry.findtext("atom:title", default="", namespaces=namespace),
            "url": link,
            "author": author.text if author is not None else None,
            "published": entry.findtext("atom:published", default=None, namespaces=namespace),
            "updated": entry.findtext("atom:updated", default=None, namespaces=namespace),
            "content_html": entry.findtext("atom:content", default=None, namespaces=namespace)
            or entry.findtext("atom:summary", default=None, namespaces=namespace),
        })
    return items


def _limit(value: int, maximum: int = 20) -> int:
    return max(1, min(value, maximum))


def _error(platform: str, exc: Exception, fallback_url: str | None = None) -> dict[str, Any]:
    detail = str(exc)
    if isinstance(exc, httpx.HTTPStatusError):
        detail = f"HTTP {exc.response.status_code}"
    elif isinstance(exc, httpx.RequestError):
        detail = "Network request failed"
    result: dict[str, Any] = {"platform": platform, "ok": False, "error": f"{type(exc).__name__}: {detail}"}
    if fallback_url:
        result["browser_fallback"] = fallback_url
    return result


@mcp.tool(annotations=READ_ONLY)
def platform_access_status() -> dict[str, Any]:
    """Show configured read-only routes and missing optional credentials."""
    return {
        "direct": {
            "github": "public REST search, issue/PR comments and line-review replies; optional GITHUB_TOKEN raises limits",
            "hacker_news": "Algolia search and indexed comment threads with parent links",
            "stack_exchange": "official public API for questions, answers, and comments",
            "v2ex": "public JSON topics/replies; reply counts checked for cache or coverage gaps",
            "youtube": "yt-dlp search; optional YOUTUBE_API_KEY uses official API",
            "bluesky": "public AppView API through api.bsky.app",
            "mastodon": "instance public timeline API",
            "reddit": "public Atom search feed; optional OAuth adds richer metadata",
            "product_hunt": "public Atom product feed; optional token adds GraphQL metadata",
            "hugging_face": "public Hub API for models, datasets, and Spaces",
            "lobsters": "public JSON feeds for focused technical discussions",
            "software_catalogs": "public npm, crates.io, Docker Hub, PyPI, GitLab, and Gitee APIs",
        },
        "credential_optional": {
            "x": bool(os.getenv("X_BEARER_TOKEN")),
            "reddit": bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET")),
            "product_hunt": bool(os.getenv("PRODUCT_HUNT_TOKEN")),
            "youtube_api": bool(os.getenv("YOUTUBE_API_KEY")),
            "github": bool(os.getenv("GITHUB_TOKEN")),
        },
        "browser_first": ["linux.do", "X without API access"],
        "write_operations": False,
    }


@mcp.tool(annotations=READ_ONLY)
def search_github(query: str, kind: str = "repositories", limit: int = 10) -> dict[str, Any]:
    """Search public GitHub repositories, issues, or users using the official REST API."""
    if kind not in {"repositories", "issues", "users"}:
        raise ValueError("kind must be repositories, issues, or users")
    headers: dict[str, str] = {"X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        data = _get_json(f"https://api.github.com/search/{kind}", params={"q": query, "per_page": _limit(limit)}, headers=headers)
        items = []
        for item in data.get("items", []):
            items.append({
                "name": item.get("full_name") or item.get("title") or item.get("login"),
                "url": item.get("html_url"),
                "description": item.get("description") or item.get("body"),
                "stars": item.get("stargazers_count"),
                "updated_at": item.get("updated_at"),
                "state": item.get("state"),
            })
        return {"platform": "github", "ok": True, "kind": kind, "total_count": data.get("total_count"), "items": items}
    except Exception as exc:
        return _error("github", exc, f"https://github.com/search?q={quote_plus(query)}&type={kind}")


@mcp.tool(annotations=READ_ONLY)
def get_github_comments(repository: str, number: int, kind: str = "discussion", page: int = 1, limit: int = 30) -> dict[str, Any]:
    """Read one page of issue/PR discussion or PR line-review comments. Repeat with page+1 if possibly_more."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or number < 1 or page < 1:
        raise ValueError("repository must be owner/repo; number and page must be positive")
    if kind not in {"discussion", "review"}:
        raise ValueError("kind must be discussion or review")
    route = "issues" if kind == "discussion" else "pulls"
    thread_url = f"https://github.com/{repository}/{'issues' if kind == 'discussion' else 'pull'}/{number}"
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        rows = _get_json(f"https://api.github.com/repos/{repository}/{route}/{number}/comments",
                         params={"per_page": _limit(limit, 100), "page": page}, headers=headers)
        items = [{
            "id": row.get("id"), "url": row.get("html_url"), "thread_url": thread_url,
            "parent_id": row.get("in_reply_to_id"),
            "parent_url": f"{thread_url}#discussion_r{row['in_reply_to_id']}" if row.get("in_reply_to_id") else thread_url,
            "author": (row.get("user") or {}).get("login"), "body_markdown": row.get("body"),
            "created_at": row.get("created_at"), "updated_at": row.get("updated_at"),
            "author_association": row.get("author_association"), "path": row.get("path"),
            "line": row.get("line"), "diff_hunk": row.get("diff_hunk"),
        } for row in rows]
        return {"platform": "github", "ok": True, "kind": kind, "thread_url": thread_url,
                "page": page, "page_size": _limit(limit, 100), "possibly_more": len(rows) == _limit(limit, 100), "items": items}
    except Exception as exc:
        return _error("github", exc, thread_url)


@mcp.tool(annotations=READ_ONLY)
def search_hacker_news(query: str, limit: int = 10, newest_first: bool = False) -> dict[str, Any]:
    """Search Hacker News stories and comments through the Algolia HN index."""
    endpoint = "search_by_date" if newest_first else "search"
    try:
        data = _get_json(f"https://hn.algolia.com/api/v1/{endpoint}", params={"query": query, "hitsPerPage": _limit(limit)})
        items = [{
            "title": hit.get("title") or hit.get("story_title") or hit.get("comment_text"),
            "url": hit.get("url") or hit.get("story_url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "author": hit.get("author"),
            "created_at": hit.get("created_at"),
            "points": hit.get("points"),
            "comments": hit.get("num_comments"),
        } for hit in data.get("hits", [])]
        return {"platform": "hacker_news", "ok": True, "items": items}
    except Exception as exc:
        return _error("hacker_news", exc, f"https://hn.algolia.com/?q={quote_plus(query)}")


@mcp.tool(annotations=READ_ONLY)
def get_hacker_news_thread(item_id: int, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Read a HN story/comment and a bounded depth-first slice of descendant comments, with parent links."""
    if item_id < 1 or offset < 0:
        raise ValueError("item_id must be positive; offset must be nonnegative")
    thread_url = f"https://news.ycombinator.com/item?id={item_id}"
    try:
        data = _get_json(f"https://hn.algolia.com/api/v1/items/{item_id}")
        stack = list(reversed(data.get("children", [])))
        comments = []
        while stack:
            row = stack.pop()
            if row.get("text"):
                comments.append({
                    "id": row.get("id"), "url": f"https://news.ycombinator.com/item?id={row.get('id')}",
                    "parent_id": row.get("parent_id"), "parent_url": f"https://news.ycombinator.com/item?id={row.get('parent_id')}",
                    "author": row.get("author"), "body_html": row.get("text"), "created_at": row.get("created_at"),
                })
            stack.extend(reversed(row.get("children", [])))
        end = offset + _limit(limit, 100)
        return {"platform": "hacker_news", "ok": True, "thread": {
            "id": data.get("id"), "url": thread_url, "title": data.get("title"), "external_url": data.get("url"),
            "author": data.get("author"), "body_html": data.get("text"), "created_at": data.get("created_at"),
        }, "items": comments[offset:end], "total_available_comments": len(comments),
            "next_offset": end if end < len(comments) else None,
            "coverage": "Algolia indexed comments with nonempty text; deleted/unindexed comments may be absent"}
    except Exception as exc:
        return _error("hacker_news", exc, thread_url)


@mcp.tool(annotations=READ_ONLY)
def search_stack_exchange(query: str, site: str = "stackoverflow", limit: int = 10) -> dict[str, Any]:
    """Search questions with the official Stack Exchange API."""
    try:
        data = _get_json("https://api.stackexchange.com/2.3/search/advanced", params={
            "q": query, "site": site, "pagesize": _limit(limit), "order": "desc", "sort": "relevance", "filter": "withbody",
        })
        items = [{
            "title": item.get("title"), "url": item.get("link"), "score": item.get("score"),
            "answers": item.get("answer_count"), "is_answered": item.get("is_answered"),
            "tags": item.get("tags"), "owner": (item.get("owner") or {}).get("display_name"),
            "creation_date": item.get("creation_date"), "body_html": item.get("body"),
        } for item in data.get("items", [])]
        return {"platform": "stack_exchange", "ok": True, "site": site, "quota_remaining": data.get("quota_remaining"), "items": items}
    except Exception as exc:
        return _error("stack_exchange", exc, f"https://stackoverflow.com/search?q={quote_plus(query)}")


@mcp.tool(annotations=READ_ONLY)
def get_stack_exchange_thread(question_id: int, site: str = "stackoverflow", limit: int = 20,
                              answer_page: int = 1, comment_page: int = 1) -> dict[str, Any]:
    """Read a question, one answer page, and comments on that question/answer page. Observe has_more/backoff_seconds."""
    if question_id < 1 or answer_page < 1 or comment_page < 1:
        raise ValueError("question_id and page numbers must be positive")
    base = "https://api.stackexchange.com/2.3"
    params = {"site": site, "filter": "withbody", "pagesize": _limit(limit, 50)}
    try:
        question_data = _get_json(f"{base}/questions/{question_id}", params=params)
        if not question_data.get("items"):
            return {"platform": "stack_exchange", "ok": False, "error": "Question not available on the selected site"}
        question = question_data["items"][0]
        question_url = question["link"]
        site_url = question_url.split("/questions/", 1)[0]
        answer_data = _get_json(f"{base}/questions/{question_id}/answers",
                                params={**params, "page": answer_page, "sort": "votes", "order": "desc"})
        answers = [{
            "id": row.get("answer_id"), "url": f"{site_url}/a/{row['answer_id']}", "parent_id": question_id,
            "parent_url": question_url, "author": (row.get("owner") or {}).get("display_name"),
            "body_html": row.get("body"), "score": row.get("score"), "is_accepted": row.get("is_accepted"),
            "created_at": row.get("creation_date"),
        } for row in answer_data.get("items", [])]
        post_ids = ";".join(str(value) for value in [question_id] + [row["id"] for row in answers])
        comment_data = _get_json(f"{base}/posts/{post_ids}/comments",
                                 params={**params, "page": comment_page, "sort": "votes", "order": "desc"})
        parent_urls = {question_id: question_url, **{row["id"]: row["url"] for row in answers}}
        comments = [{
            "id": row.get("comment_id"), "url": f"{parent_urls[row['post_id']]}#comment{row['comment_id']}_{row['post_id']}",
            "parent_id": row.get("post_id"), "parent_url": parent_urls[row["post_id"]],
            "author": (row.get("owner") or {}).get("display_name"), "body_html": row.get("body"),
            "score": row.get("score"), "created_at": row.get("creation_date"),
        } for row in comment_data.get("items", [])]
        return {"platform": "stack_exchange", "ok": True, "site": site, "question": {
            "id": question_id, "url": question_url, "title": question.get("title"), "body_html": question.get("body"),
            "author": (question.get("owner") or {}).get("display_name"), "answer_count": question.get("answer_count"),
        }, "answers": answers, "comments": comments, "answer_page": answer_page, "comment_page": comment_page,
            "answers_has_more": answer_data.get("has_more"), "comments_has_more": comment_data.get("has_more"),
            "quota_remaining": comment_data.get("quota_remaining"),
            "backoff_seconds": max(value.get("backoff", 0) for value in (question_data, answer_data, comment_data))}
    except Exception as exc:
        return _error("stack_exchange", exc)


@mcp.tool(annotations=READ_ONLY)
def get_v2ex_feed(feed: str = "hot", limit: int = 10) -> dict[str, Any]:
    """Read V2EX hot or latest topics from its public JSON API."""
    if feed not in {"hot", "latest"}:
        raise ValueError("feed must be hot or latest")
    try:
        data = _get_json(f"https://www.v2ex.com/api/topics/{feed}.json")
        items = [{
            "id": item.get("id"), "title": item.get("title"), "url": item.get("url"),
            "content": item.get("content"), "replies": item.get("replies"),
            "member": (item.get("member") or {}).get("username"),
            "node": (item.get("node") or {}).get("title"), "created": item.get("created"),
        } for item in data[:_limit(limit)]]
        return {"platform": "v2ex", "ok": True, "feed": feed, "items": items}
    except Exception as exc:
        return _error("v2ex", exc, "https://www.v2ex.com/?tab=tech")


@mcp.tool(annotations=READ_ONLY)
def get_v2ex_topic(topic_id: int, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Read a V2EX topic and a bounded slice of public replies, with author and source links."""
    if topic_id < 1 or offset < 0:
        raise ValueError("topic_id must be positive; offset must be nonnegative")
    thread_url = f"https://www.v2ex.com/t/{topic_id}"
    try:
        topics = _get_json("https://www.v2ex.com/api/topics/show.json", params={"id": topic_id})
        replies = _get_json("https://www.v2ex.com/api/replies/show.json", params={"topic_id": topic_id})
        end = offset + _limit(limit, 100)
        items = [{**row, "author": (row.get("member") or {}).get("username"),
                  "url": f"{thread_url}#r_{row['id']}", "parent_id": topic_id, "parent_url": thread_url}
                 for row in replies[offset:end]]
        return {"platform": "v2ex", "ok": True, "topic": topics[0] if topics else None, "replies": items,
                "returned_by_api": len(replies), "next_offset": end if end < len(replies) else None,
                "api_reply_count_mismatch": bool(topics and topics[0].get("replies", 0) != len(replies)),
                "browser_fallback": thread_url,
                "coverage": "Slice of replies returned by the public endpoint; compare returned_by_api with topic.replies"}
    except Exception as exc:
        return _error("v2ex", exc, f"https://www.v2ex.com/t/{topic_id}")


def _youtube_via_api(query: str, limit: int) -> dict[str, Any]:
    data = _get_json("https://www.googleapis.com/youtube/v3/search", params={
        "part": "snippet", "type": "video", "q": query, "maxResults": _limit(limit), "key": os.environ["YOUTUBE_API_KEY"],
    })
    items = [{
        "id": (item.get("id") or {}).get("videoId"),
        "url": f"https://www.youtube.com/watch?v={(item.get('id') or {}).get('videoId')}",
        "title": (item.get("snippet") or {}).get("title"),
        "channel": (item.get("snippet") or {}).get("channelTitle"),
        "published_at": (item.get("snippet") or {}).get("publishedAt"),
        "description": (item.get("snippet") or {}).get("description"),
    } for item in data.get("items", [])]
    return {"platform": "youtube", "ok": True, "route": "official_api", "items": items}


def _youtube_via_ytdlp(query: str, limit: int) -> dict[str, Any]:
    executable = shutil.which("yt-dlp")
    if not executable:
        raise RuntimeError("yt-dlp is not installed or not on PATH")
    command = [executable, "--flat-playlist", "--dump-single-json", "--skip-download", f"ytsearch{_limit(limit)}:{query}"]
    completed = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
        check=True,
    )
    data = json.loads(completed.stdout)
    items = [{
        "id": item.get("id"), "url": item.get("url") or item.get("webpage_url"), "title": item.get("title"),
        "channel": item.get("channel") or item.get("uploader"), "duration": item.get("duration"),
        "view_count": item.get("view_count"), "description": item.get("description"),
    } for item in data.get("entries", [])]
    return {"platform": "youtube", "ok": True, "route": "yt-dlp", "items": items}


@mcp.tool(annotations=READ_ONLY)
def search_youtube(query: str, limit: int = 10) -> dict[str, Any]:
    """Search YouTube read-only; use the official API key when present, otherwise yt-dlp."""
    try:
        return _youtube_via_api(query, limit) if os.getenv("YOUTUBE_API_KEY") else _youtube_via_ytdlp(query, limit)
    except Exception as exc:
        return _error("youtube", exc, f"https://www.youtube.com/results?search_query={quote_plus(query)}")


@mcp.tool(annotations=READ_ONLY)
def search_bluesky(query: str, limit: int = 10) -> dict[str, Any]:
    """Search public Bluesky posts through the public AppView API."""
    try:
        data = _get_json("https://api.bsky.app/xrpc/app.bsky.feed.searchPosts", params={"q": query, "limit": _limit(limit)})
        items = [{
            "uri": post.get("uri"), "cid": post.get("cid"), "author": (post.get("author") or {}).get("handle"),
            "text": ((post.get("record") or {}).get("text")), "created_at": ((post.get("record") or {}).get("createdAt")),
            "likes": post.get("likeCount"), "reposts": post.get("repostCount"), "replies": post.get("replyCount"),
        } for post in data.get("posts", [])]
        return {"platform": "bluesky", "ok": True, "route": "public_appview", "items": items}
    except Exception as exc:
        return _error("bluesky", exc, f"https://bsky.app/search?q={quote_plus(query)}")


def _safe_instance(instance: str) -> str:
    hostname = instance.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
    if not re.fullmatch(r"[a-z0-9.-]+", hostname) or "." not in hostname:
        raise ValueError("instance must be a public hostname")
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValueError("private instances are not allowed")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return hostname
    raise ValueError("IP-address instances are not allowed")


@mcp.tool(annotations=READ_ONLY)
def get_mastodon_public(instance: str = "fosstodon.org", limit: int = 10, local_only: bool = False) -> dict[str, Any]:
    """Read an instance's public Mastodon timeline; availability is instance-dependent."""
    hostname = _safe_instance(instance)
    try:
        params: dict[str, Any] = {"limit": _limit(limit)}
        if local_only:
            params["local"] = "true"
        data = _get_json(f"https://{hostname}/api/v1/timelines/public", params=params)
        items = [{
            "id": item.get("id"), "url": item.get("url"), "author": (item.get("account") or {}).get("acct"),
            "created_at": item.get("created_at"), "content_html": item.get("content"),
            "replies": item.get("replies_count"), "reblogs": item.get("reblogs_count"), "favourites": item.get("favourites_count"),
        } for item in data]
        return {"platform": "mastodon", "ok": True, "instance": hostname, "items": items}
    except Exception as exc:
        return _error("mastodon", exc, f"https://{hostname}/public/local")


@mcp.tool(annotations=READ_ONLY)
def search_x(query: str, limit: int = 10, next_token: str = "") -> dict[str, Any]:
    """Read one page of X posts from the last 7 days; API page size is 10–100."""
    token = os.getenv("X_BEARER_TOKEN")
    fallback = f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
    if not token:
        return {
            "platform": "x", "ok": False, "needs_credentials": "X_BEARER_TOKEN",
            "browser_fallback": fallback, "web_search_query": f"site:x.com {query}",
            "note": "Browser sign-in and official API credentials are separate; check browser availability independently.",
        }
    try:
        page_size = max(10, _limit(limit, 100))
        params = {
            "query": query, "max_results": page_size,
            "tweet.fields": "author_id,created_at,public_metrics,lang,conversation_id",
            "expansions": "author_id", "user.fields": "username,name",
        }
        if next_token:
            params["next_token"] = next_token
        data = _get_json("https://api.x.com/2/tweets/search/recent", params=params,
                         headers={"Authorization": f"Bearer {token}"})
        authors = {user["id"]: user for user in data.get("includes", {}).get("users", [])}
        items = []
        for post in data.get("data", []):
            author = authors.get(post.get("author_id"), {})
            items.append({**post, "author": author,
                          "url": f"https://x.com/i/web/status/{post['id']}"})
        # Preserve the entire page: truncating to limit<10 would skip posts at the next cursor.
        return {"platform": "x", "ok": "data" in data or "meta" in data,
                "items": items, "meta": data.get("meta"), "errors": data.get("errors", []),
                "page_size": page_size, "coverage": "recent_7_days", "browser_fallback": fallback}
    except Exception as exc:
        return _error("x", exc, fallback)


@mcp.tool(annotations=READ_ONLY)
def search_reddit(query: str, subreddit: str = "", limit: int = 10) -> dict[str, Any]:
    """Search Reddit read-only; use OAuth when configured, otherwise the public Atom feed."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", USER_AGENT)
    fallback = f"https://www.reddit.com/search/?q={quote_plus(query)}"
    if not client_id or not client_secret:
        if subreddit and not re.fullmatch(r"[A-Za-z0-9_]+", subreddit):
            raise ValueError("subreddit contains invalid characters")
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.rss" if subreddit else "https://www.reddit.com/search.rss"
            params = {"q": query, "sort": "relevance"}
            if subreddit:
                params["restrict_sr"] = "on"
            items = _atom_items(_get_text(url, params=params, headers={"User-Agent": user_agent}), limit)
            return {"platform": "reddit", "ok": True, "route": "public_atom", "items": items}
        except Exception as exc:
            return _error("reddit", exc, fallback)
    try:
        with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": user_agent}) as client:
            auth = client.post("https://www.reddit.com/api/v1/access_token", data={"grant_type": "client_credentials"}, auth=(client_id, client_secret))
            auth.raise_for_status()
            token = auth.json()["access_token"]
            path = f"r/{subreddit}/search" if subreddit else "search"
            response = client.get(f"https://oauth.reddit.com/{path}", params={"q": query, "limit": _limit(limit), "restrict_sr": bool(subreddit)}, headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            children = response.json().get("data", {}).get("children", [])
        items = [{
            "title": child["data"].get("title"), "url": "https://www.reddit.com" + child["data"].get("permalink", ""),
            "subreddit": child["data"].get("subreddit"), "author": child["data"].get("author"),
            "score": child["data"].get("score"), "comments": child["data"].get("num_comments"),
            "created_utc": child["data"].get("created_utc"), "selftext": child["data"].get("selftext"),
        } for child in children]
        return {"platform": "reddit", "ok": True, "route": "official_oauth", "items": items}
    except Exception as exc:
        return _error("reddit", exc, fallback)


@mcp.tool(annotations=READ_ONLY)
def get_product_hunt_posts(limit: int = 10) -> dict[str, Any]:
    """Read current Product Hunt posts; use GraphQL when configured, otherwise the public Atom feed."""
    token = os.getenv("PRODUCT_HUNT_TOKEN")
    fallback = "https://www.producthunt.com/"
    if not token:
        try:
            items = _atom_items(_get_text("https://www.producthunt.com/feed"), limit)
            return {"platform": "product_hunt", "ok": True, "route": "public_atom", "items": items}
        except Exception as exc:
            return _error("product_hunt", exc, fallback)
    query = "query Posts($first: Int!) { posts(first: $first, order: RANKING) { nodes { id name tagline description url website votesCount createdAt } } }"
    try:
        data = _post_json("https://api.producthunt.com/v2/api/graphql", json_body={"query": query, "variables": {"first": _limit(limit)}}, headers={"Authorization": f"Bearer {token}"})
        return {"platform": "product_hunt", "ok": "errors" not in data, "route": "official_graphql", "items": (((data.get("data") or {}).get("posts") or {}).get("nodes") or []), "errors": data.get("errors")}
    except Exception as exc:
        return _error("product_hunt", exc, fallback)


@mcp.tool(annotations=READ_ONLY)
def linux_do_search_route(query: str) -> dict[str, Any]:
    """Return deterministic Linux.do discovery routes when direct API access is Cloudflare-protected."""
    return {
        "platform": "linux.do", "ok": True, "route": "site_restricted_web_search_then_browser",
        "web_search_query": f"site:linux.do {query}",
        "site_search_url": f"https://linux.do/search?q={quote_plus(query)}",
        "reason": "This tool returns discovery routes only; verify search results and readable posts in the user's normal browser.",
    }


@mcp.tool(annotations=READ_ONLY)
def search_hugging_face(query: str, resource: str = "models", limit: int = 10) -> dict[str, Any]:
    """Search public Hugging Face models, datasets, or Spaces through the Hub API."""
    if resource not in {"models", "datasets", "spaces"}:
        raise ValueError("resource must be models, datasets, or spaces")
    try:
        data = _get_json(f"https://huggingface.co/api/{resource}", params={
            "search": query, "limit": _limit(limit), "sort": "downloads", "direction": "-1",
        })
        prefix = "" if resource == "models" else f"{resource}/"
        items = [{
            "id": item.get("id"), "url": f"https://huggingface.co/{prefix}{item.get('id')}",
            "downloads": item.get("downloads"), "likes": item.get("likes"),
            "updated_at": item.get("lastModified"), "tags": item.get("tags"),
            "pipeline_tag": item.get("pipeline_tag"),
        } for item in data]
        return {"platform": "hugging_face", "ok": True, "resource": resource, "items": items}
    except Exception as exc:
        return _error("hugging_face", exc, f"https://huggingface.co/{resource}?search={quote_plus(query)}")


@mcp.tool(annotations=READ_ONLY)
def get_lobsters_feed(feed: str = "hottest", limit: int = 10) -> dict[str, Any]:
    """Read Lobsters hottest or newest technical stories through its public JSON feed."""
    if feed not in {"hottest", "newest"}:
        raise ValueError("feed must be hottest or newest")
    try:
        data = _get_json(f"https://lobste.rs/{feed}.json")
        items = [{
            "title": item.get("title"), "url": item.get("url"), "discussion_url": item.get("comments_url"),
            "score": item.get("score"), "comments": item.get("comment_count"), "submitter": item.get("submitter_user"),
            "created_at": item.get("created_at"), "tags": item.get("tags"), "description": item.get("description"),
        } for item in data[:_limit(limit)]]
        return {"platform": "lobsters", "ok": True, "feed": feed, "items": items}
    except Exception as exc:
        return _error("lobsters", exc, f"https://lobste.rs/{feed}")


@mcp.tool(annotations=READ_ONLY)
def search_packages(query: str, registry: str = "npm", limit: int = 10) -> dict[str, Any]:
    """Search npm, crates.io, or Docker Hub packages/images through public APIs."""
    if registry not in {"npm", "crates", "dockerhub"}:
        raise ValueError("registry must be npm, crates, or dockerhub")
    try:
        if registry == "npm":
            data = _get_json("https://registry.npmjs.org/-/v1/search", params={"text": query, "size": _limit(limit)})
            items = [{
                "name": (row.get("package") or {}).get("name"), "version": (row.get("package") or {}).get("version"),
                "description": (row.get("package") or {}).get("description"), "url": (row.get("package") or {}).get("links", {}).get("npm"),
                "updated_at": (row.get("package") or {}).get("date"), "score": row.get("score", {}).get("final"),
            } for row in data.get("objects", [])]
        elif registry == "crates":
            data = _get_json("https://crates.io/api/v1/crates", params={"q": query, "per_page": _limit(limit)})
            items = [{
                "name": row.get("id"), "version": row.get("newest_version"), "description": row.get("description"),
                "url": f"https://crates.io/crates/{row.get('id')}", "downloads": row.get("downloads"),
                "updated_at": row.get("updated_at"),
            } for row in data.get("crates", [])]
        else:
            data = _get_json("https://hub.docker.com/v2/search/repositories/", params={"query": query, "page_size": _limit(limit)})
            items = [{
                "name": row.get("repo_name"), "description": row.get("short_description"),
                "url": f"https://hub.docker.com/r/{row.get('repo_name')}", "stars": row.get("star_count"),
                "pulls": row.get("pull_count"), "official": row.get("is_official"), "automated": row.get("is_automated"),
            } for row in data.get("summaries", data.get("results", []))]
        return {"platform": registry, "ok": True, "items": items}
    except Exception as exc:
        return _error(registry, exc)


@mcp.tool(annotations=READ_ONLY)
def get_pypi_package(package: str) -> dict[str, Any]:
    """Read exact PyPI package metadata and release history through the official JSON API."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", package):
        raise ValueError("invalid PyPI package name")
    try:
        data = _get_json(f"https://pypi.org/pypi/{package}/json")
        info = data.get("info", {})
        return {"platform": "pypi", "ok": True, "package": {
            "name": info.get("name"), "version": info.get("version"), "summary": info.get("summary"),
            "project_url": info.get("project_url"), "home_page": info.get("home_page"),
            "requires_python": info.get("requires_python"), "requires_dist": info.get("requires_dist"),
            "classifiers": info.get("classifiers"), "release_versions": list(data.get("releases", {}).keys())[-20:],
        }}
    except Exception as exc:
        return _error("pypi", exc, f"https://pypi.org/project/{quote_plus(package)}/")


@mcp.tool(annotations=READ_ONLY)
def search_code_hosts(query: str, host: str = "gitlab", limit: int = 10) -> dict[str, Any]:
    """Search public GitLab or Gitee repositories through their public APIs."""
    if host not in {"gitlab", "gitee"}:
        raise ValueError("host must be gitlab or gitee")
    try:
        if host == "gitlab":
            data = _get_json("https://gitlab.com/api/v4/projects", params={
                "search": query, "simple": "true", "per_page": _limit(limit), "order_by": "star_count", "sort": "desc",
            })
            items = [{
                "name": row.get("path_with_namespace"), "url": row.get("web_url"), "description": row.get("description"),
                "stars": row.get("star_count"), "forks": row.get("forks_count"), "updated_at": row.get("last_activity_at"),
            } for row in data]
        else:
            data = _get_json("https://gitee.com/api/v5/search/repositories", params={"q": query, "per_page": _limit(limit)})
            items = [{
                "name": row.get("full_name"), "url": row.get("html_url"), "description": row.get("description"),
                "stars": row.get("stargazers_count"), "forks": row.get("forks_count"), "updated_at": row.get("updated_at"),
            } for row in data]
        return {"platform": host, "ok": True, "items": items}
    except Exception as exc:
        fallback_host = "gitlab.com" if host == "gitlab" else "gitee.com"
        return _error(host, exc, f"https://{fallback_host}/search?search={quote_plus(query)}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
