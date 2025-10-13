#!/usr/bin/env python3
import asyncio
import json


async def test_mcp():
    proc = await asyncio.create_subprocess_exec(
        "uv",
        "tool",
        "run",
        "arxiv-mcp-server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Initialize
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

    # Tools list
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    requests = json.dumps(init_req) + "\n" + json.dumps(tools_req) + "\n"

    try:
        out, err = await asyncio.wait_for(
            proc.communicate(requests.encode()), timeout=10
        )

        lines = out.decode().strip().split("\n")
        for line in lines:
            if line.strip():
                resp = json.loads(line)
                if resp.get("id") == 2:  # tools/list response
                    tools = resp.get("result", {}).get("tools", [])
                    print(f"Available tools: {len(tools)}")
                    for tool in tools:
                        print(f"- {tool['name']}: {tool.get('description', '')}")
                        if "inputSchema" in tool:
                            props = tool["inputSchema"].get("properties", {})
                            print(f"  Parameters: {list(props.keys())}")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test_mcp())
