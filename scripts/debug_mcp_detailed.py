#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.mcp_arxiv import _invoke


async def debug_detailed():
    print("🔍 詳細なMCPデバッグ開始")

    # 1. search_papers
    print("\n1️⃣ search_papers テスト")
    try:
        result = await _invoke(
            "search_papers", {"query": "attention", "max_results": 2}
        )
        print(f"✅ search_papers レスポンス: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ search_papers エラー: {e}")

    # 2. download_paper
    print("\n2️⃣ download_paper テスト")
    try:
        result = await _invoke("download_paper", {"paper_id": "1706.03762"})
        print(f"✅ download_paper レスポンス: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ download_paper エラー: {e}")

    # 3. list_papers
    print("\n3️⃣ list_papers テスト")
    try:
        result = await _invoke("list_papers", {})
        print(f"✅ list_papers レスポンス: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ list_papers エラー: {e}")

    # 4. read_paper
    print("\n4️⃣ read_paper テスト")
    try:
        result = await _invoke("read_paper", {"paper_id": "1706.03762"})
        print(f"✅ read_paper レスポンス型: {type(result)}")
        if isinstance(result, list):
            print(f"   リスト長: {len(result)}")
            if len(result) > 0:
                print(f"   最初の要素: {type(result[0])}")
                print(f"   最初の要素内容: {str(result[0])[:200]}...")
        else:
            print(f"   内容: {str(result)[:200]}...")
    except Exception as e:
        print(f"❌ read_paper エラー: {e}")


asyncio.run(debug_detailed())
