"""Protocol-level smoke test for the local platform_research MCP server."""

import asyncio
import argparse
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve().with_name('server.py'))],
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    calls = {
        "platform_access_status": {},
        "search_github": {"query": "model context protocol", "limit": 2},
        "search_hacker_news": {"query": "model context protocol", "limit": 2},
        "search_stack_exchange": {"query": "model context protocol", "limit": 2},
        "get_v2ex_feed": {"feed": "hot", "limit": 2},
        "search_youtube": {"query": "model context protocol", "limit": 2},
        "search_bluesky": {"query": "model context protocol", "limit": 2},
        "get_mastodon_public": {"instance": "fosstodon.org", "limit": 2},
        "search_x": {"query": "model context protocol", "limit": 2},
        "search_reddit": {"query": "model context protocol", "limit": 2},
        "get_product_hunt_posts": {"limit": 2},
        "linux_do_search_route": {"query": "MCP"},
        "search_hugging_face": {"query": "qwen", "resource": "models", "limit": 2},
        "get_lobsters_feed": {"feed": "hottest", "limit": 2},
        "search_packages": {"query": "model context protocol", "registry": "npm", "limit": 2},
        "get_pypi_package": {"package": "mcp"},
        "search_code_hosts": {"query": "model context protocol", "host": "gitlab", "limit": 2},
    }
    summary = {}
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            summary["tool_count"] = len(listed.tools)
            summary["read_only_tool_count"] = sum(
                1 for tool in listed.tools if tool.annotations and tool.annotations.readOnlyHint is True
            )
            for name, arguments in calls.items():
                try:
                    result = await session.call_tool(name, arguments)
                    if result.isError:
                        raise RuntimeError('MCP tool returned an error')
                    payload = json.loads(result.content[0].text)
                    items = payload.get('items', [])
                    if payload.get('needs_credentials'):
                        status = 'needs_credentials'
                    elif payload.get('ok') is False:
                        status = 'failed'
                    elif name == 'platform_access_status':
                        status = 'configuration_only'
                    elif name == 'linux_do_search_route':
                        status = 'route_only'
                    elif name == 'get_pypi_package' and payload.get('package', {}).get('name'):
                        status = 'metadata_read'
                    else:
                        status = 'items_read' if items else 'empty'
                    summary[name] = {
                        'status': status, 'count': len(items),
                        'needs_credentials': payload.get('needs_credentials'),
                        'route': payload.get('route'), 'error': payload.get('error'),
                    }
                except Exception as exc:
                    summary[name] = {'status': 'failed', 'error': str(exc) or type(exc).__name__}
                if args.out:
                    args.out.parent.mkdir(parents=True, exist_ok=True)
                    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
