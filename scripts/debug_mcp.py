#!/usr/bin/env python3
"""
MCP arxiv-mcp-server デバッグスクリプト
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.mcp_arxiv import _invoke


async def debug_mcp_tools():
    """MCPツールの詳細をデバッグ"""
    print("🔍 MCP arxiv-mcp-server デバッグ開始")

    # 1. ツールリストを取得
    print("\n1️⃣ 利用可能なツールを確認")
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv",
            "tool",
            "run",
            "arxiv-mcp-server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # tools/list リクエスト
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        out, err = await asyncio.wait_for(
            proc.communicate(json.dumps(req).encode()), timeout=30
        )

        if out:
            resp = json.loads(out.decode())
            print(f"✅ レスポンス: {json.dumps(resp, indent=2)}")

            if "result" in resp and "tools" in resp["result"]:
                tools = resp["result"]["tools"]
                print(f"\n📋 利用可能なツール ({len(tools)}個):")
                for tool in tools:
                    name = tool.get("name", "Unknown")
                    desc = tool.get("description", "No description")
                    print(f"  - {name}: {desc}")

                    # パラメータ情報
                    if "inputSchema" in tool:
                        schema = tool["inputSchema"]
                        if "properties" in schema:
                            props = schema["properties"]
                            print(f"    パラメータ: {list(props.keys())}")
        else:
            print(f"❌ 空のレスポンス. stderr: {err.decode()}")

    except Exception as e:
        print(f"❌ ツールリスト取得失敗: {e}")

    # 2. 個別ツールのテスト
    print("\n2️⃣ 個別ツールのテスト")

    # search_papers のテスト
    print("\n🔍 search_papers テスト")
    try:
        result = await _invoke(
            "search_papers", {"query": "attention mechanism", "max_results": 2}
        )
        print(f"✅ search_papers 成功: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ search_papers 失敗: {e}")

    # list_papers のテスト
    print("\n📋 list_papers テスト")
    try:
        result = await _invoke("list_papers", {})
        print(f"✅ list_papers 成功: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ list_papers 失敗: {e}")

    # download_paper のテスト
    print("\n⬇️ download_paper テスト")
    try:
        result = await _invoke("download_paper", {"paper_id": "1706.03762"})
        print(f"✅ download_paper 成功: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ download_paper 失敗: {e}")

    # read_paper のテスト（ダウンロード後）
    print("\n📖 read_paper テスト")
    try:
        result = await _invoke("read_paper", {"paper_id": "1706.03762"})
        content = result.get("content", "")
        print(f"✅ read_paper 成功: {len(content)}文字のコンテンツ")
        if content:
            print(f"   プレビュー: {content[:200]}...")
    except Exception as e:
        print(f"❌ read_paper 失敗: {e}")


async def main():
    try:
        await debug_mcp_tools()
    except KeyboardInterrupt:
        print("\n⏹️ デバッグが中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
