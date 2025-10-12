from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Optional

ENABLE = os.getenv("ARXIV_MCP_ENABLE", "false").lower() == "true"
STORAGE = os.getenv("ARXIV_STORAGE_PATH", os.path.expanduser("~/.arxiv-mcp-server/papers"))
CMD = os.getenv("ARXIV_MCP_CMD", "uv")
ARGS = os.getenv("ARXIV_MCP_ARGS", "tool run arxiv-mcp-server").split()
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
        
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": params},
        }
        
        out, err = await asyncio.wait_for(
            proc.communicate(json.dumps(req).encode()), timeout=TIMEOUT
        )
        
        if not out:
            raise MCPArxivError(f"Empty response from MCP server. stderr: {err.decode()}")
        
        resp = json.loads(out.decode())
        if "error" in resp:
            raise MCPArxivError(str(resp["error"]))
        
        return resp.get("result") or {}
    except asyncio.TimeoutError as e:
        raise MCPArxivError(f"MCP tool call timed out after {TIMEOUT}s") from e
    except json.JSONDecodeError as e:
        raise MCPArxivError(f"Invalid JSON response from MCP server") from e
    except Exception as e:
        raise MCPArxivError(f"MCP invocation failed: {str(e)}") from e


async def mcp_download_paper(arxiv_id: str) -> bool:
    try:
        r = await _invoke("download_paper", {"id": arxiv_id})
        return bool(r.get("ok", True))
    except MCPArxivError:
        return False


async def mcp_read_paper(arxiv_id: str, fmt: str = "plain") -> str:
    r = await _invoke("read_paper", {"id": arxiv_id, "format": fmt})
    return r.get("content", "")
