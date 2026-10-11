"""Live, read-only MCP checks for discussion bodies, provenance, and pagination."""

import asyncio
import argparse
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Save all checks, including failures')
    args = parser.parse_args()
    params = StdioServerParameters(
        command=sys.executable, args=[str(root / "server.py")],
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    cases = [
        ("get_hacker_news_thread", {"item_id": 8863, "limit": 3}, "items", "body_html"),
        ("get_github_comments", {"repository": "microsoft/TypeScript", "number": 9998, "limit": 3}, "items", "body_markdown"),
        ("get_github_comments", {"repository": "microsoft/TypeScript", "number": 26, "kind": "review", "limit": 3}, "items", "body_markdown"),
        ("get_stack_exchange_thread", {"question_id": 11227809, "limit": 3}, "comments", "body_html"),
        ("get_v2ex_topic", {"topic_id": 316762, "limit": 3}, "replies", "content"),
    ]
    summary = []
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            assert all(tool.annotations and tool.annotations.readOnlyHint for tool in listed.tools)
            for name, arguments, key, body in cases:
                check = {"tool": name, "kind": arguments.get("kind"), "ok": False}
                try:
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, 'MCP tool returned an error'
                    payload = json.loads(result.content[0].text)
                    assert payload.get("ok"), payload.get("error", 'missing success status')
                    rows = payload[key]
                    assert 0 < len(rows) <= 3, f'unexpected row count: {len(rows)}'
                    assert all(row.get(body) and "author" in row and row["url"].startswith("https://")
                               and row["parent_url"].startswith("https://") for row in rows), 'missing body or provenance'
                    if name == "get_stack_exchange_thread":
                        assert payload["answers"] and all(row.get("body_html") for row in payload["answers"])
                    check.update(count=len(rows), body_characters=sum(len(row[body]) for row in rows),
                                 example_url=rows[0]["url"], api_reply_count_mismatch=payload.get("api_reply_count_mismatch"))
                    if name == "get_hacker_news_thread":
                        assert payload.get("next_offset") is not None, 'fixture has no next page'
                        result = await session.call_tool(name, {**arguments, "offset": payload["next_offset"]})
                        assert not result.isError, 'pagination returned an MCP error'
                        following = json.loads(result.content[0].text)
                        assert following.get("ok") and following["items"], 'pagination has no readable rows'
                        assert set(row["id"] for row in rows).isdisjoint(row["id"] for row in following["items"]), 'duplicate page'
                        check['pagination_verified'] = True
                    check['ok'] = True
                except Exception as exc:
                    check['error'] = str(exc) or type(exc).__name__
                summary.append(check)
                if args.out:
                    args.out.parent.mkdir(parents=True, exist_ok=True)
                    args.out.write_text(json.dumps({"read_only_tools": len(listed.tools), "checks": summary}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({"read_only_tools": len(listed.tools), "checks": summary}, ensure_ascii=True, indent=2))
    return int(any(not check['ok'] for check in summary))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
