from __future__ import annotations

import asyncio
import hashlib
import json
import os

ENABLE = os.getenv("ARXIV_MCP_ENABLE", "false").lower() == "true"

# ストレージパスの設定（環境に関係なく統一）
STORAGE = os.getenv("ARXIV_STORAGE_PATH", "/app/arxiv-papers")

# ローカル開発環境の場合のみホームディレクトリを使用
if not os.path.exists("/app") and os.path.expanduser("~") != "/":
    STORAGE = os.getenv(
        "ARXIV_STORAGE_PATH", os.path.expanduser("~/.arxiv-mcp-server/papers")
    )

CMD = os.getenv("ARXIV_MCP_CMD", "uv")
ARGS = ["tool", "run", "arxiv-mcp-server", "--storage-path", STORAGE]
TIMEOUT = int(os.getenv("ARXIV_MCP_TIMEOUT_S", "60"))


class MCPArxivError(Exception):
    pass


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


async def _invoke(tool: str, params: dict) -> dict:
    if not ENABLE:
        raise MCPArxivError("MCP disabled via ARXIV_MCP_ENABLE")

    try:
        proc = await asyncio.create_subprocess_exec(
            CMD,
            *ARGS,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 1. Initialize the MCP server
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "papers-rag-agent", "version": "1.0"},
            },
        }

        # 2. Send initialized notification
        initialized_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        # 3. Tool call request
        tool_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool, "arguments": params},
        }

        # Send all requests
        requests = (
            json.dumps(init_req)
            + "\n"
            + json.dumps(initialized_notif)
            + "\n"
            + json.dumps(tool_req)
            + "\n"
        )

        out, err = await asyncio.wait_for(
            proc.communicate(requests.encode()), timeout=TIMEOUT
        )

        if not out:
            raise MCPArxivError(
                f"Empty response from MCP server. stderr: {err.decode()}"
            )

        # Parse multiple JSON responses
        lines = out.decode().strip().split("\n")
        tool_response = None

        for line in lines:
            if line.strip():
                resp = json.loads(line)
                if resp.get("id") == 2:  # Tool call response
                    tool_response = resp
                    break

        if not tool_response:
            raise MCPArxivError("No tool response received")

        if "error" in tool_response:
            raise MCPArxivError(str(tool_response["error"]))

        return tool_response.get("result") or {}
    except asyncio.TimeoutError as e:
        raise MCPArxivError(f"MCP tool call timed out after {TIMEOUT}s") from e
    except json.JSONDecodeError as e:
        raise MCPArxivError("Invalid JSON response from MCP server") from e
    except Exception as e:
        raise MCPArxivError(f"MCP invocation failed: {str(e)}") from e


async def mcp_download_paper(arxiv_id: str) -> bool:
    try:
        r = await _invoke("download_paper", {"paper_id": arxiv_id})
        # Check if the response indicates success
        if isinstance(r, dict) and "content" in r:
            content = r["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                return "successfully" in text.lower() or "downloaded" in text.lower()
        return False
    except MCPArxivError:
        return False


async def mcp_read_paper(arxiv_id: str, fmt: str = "plain") -> str:
    # Note: arxiv-mcp-server's read_paper doesn't support format parameter
    # It returns the content in markdown format
    try:
        r = await _invoke("read_paper", {"paper_id": arxiv_id})
        # The response format: {"content": [{"type": "text", "text": "..."}], "isError": false}
        if isinstance(r, dict) and "content" in r:
            content = r["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        return ""
    except MCPArxivError:
        return ""


async def mcp_search_papers(
    query: str,
    max_results: int = 10,
    date_from: str | None = None,
    categories: list | None = None,
) -> list:
    """Search for papers using MCP arxiv-mcp-server"""
    if not ENABLE:
        raise MCPArxivError(
            "MCP is disabled. Set ARXIV_MCP_ENABLE=true to enable full functionality."
        )

    params = {"query": query, "max_results": max_results}
    if date_from:
        params["date_from"] = date_from
    if categories:
        params["categories"] = categories

    r = await _invoke("search_papers", params)
    # Parse the JSON response from the content
    if isinstance(r, dict) and "content" in r:
        content = r["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
            import json

            data = json.loads(text)
            return data.get("papers", [])
    return []


async def mcp_list_papers() -> list:
    """List all downloaded papers using MCP arxiv-mcp-server"""
    try:
        r = await _invoke("list_papers", {})
        # Parse the JSON response from the content
        if isinstance(r, dict) and "content" in r:
            content = r["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                import json

                data = json.loads(text)
                return data.get("papers", [])
        return []
    except (MCPArxivError, json.JSONDecodeError):
        return []
