#!/usr/bin/env python3
import asyncio
import json


async def test_mcp_direct():
    print("🔍 直接MCPサーバーテスト")

    proc = await asyncio.create_subprocess_exec(
        "uv",
        "tool",
        "run",
        "arxiv-mcp-server",
        "--storage-path",
        "/Users/toshi/.arxiv-mcp-server/papers",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    }

    # 2. Initialized notification
    initialized_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }

    # 3. List tools
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    # 4. Search papers
    search_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_papers",
            "arguments": {"query": "attention mechanism", "max_results": 2},
        },
    }

    requests = (
        json.dumps(init_req)
        + "\n"
        + json.dumps(initialized_notif)
        + "\n"
        + json.dumps(tools_req)
        + "\n"
        + json.dumps(search_req)
        + "\n"
    )

    try:
        out, err = await asyncio.wait_for(
            proc.communicate(requests.encode()), timeout=30
        )

        print("📤 送信したリクエスト:")
        print("  1. initialize")
        print("  2. tools/list")
        print("  3. tools/call search_papers")

        print("\n📥 受信したレスポンス:")
        lines = out.decode().strip().split("\n")
        for i, line in enumerate(lines, 1):
            if line.strip():
                resp = json.loads(line)
                print(
                    f"  {i}. ID={resp.get('id')}: {resp.get('result', resp.get('error', 'Unknown'))}"
                )

                # ツールリストの詳細表示
                if resp.get("id") == 2 and "result" in resp:
                    tools = resp["result"].get("tools", [])
                    print(f"     利用可能なツール: {len(tools)}個")
                    for tool in tools:
                        print(
                            f"       - {tool.get('name')}: {tool.get('description', '')}"
                        )

                # 検索結果の詳細表示
                if resp.get("id") == 3:
                    if "result" in resp:
                        result = resp["result"]
                        if isinstance(result, list):
                            print(f"     検索結果: {len(result)}件")
                            for item in result[:2]:
                                if isinstance(item, dict) and "text" in item:
                                    text = (
                                        item["text"][:100] + "..."
                                        if len(item["text"]) > 100
                                        else item["text"]
                                    )
                                    print(f"       - {text}")
                    elif "error" in resp:
                        print(f"     エラー: {resp['error']}")

        if err:
            print(f"\n⚠️ stderr: {err.decode()}")

    except Exception as e:
        print(f"❌ エラー: {e}")


asyncio.run(test_mcp_direct())
