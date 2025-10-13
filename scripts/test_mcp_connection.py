#!/usr/bin/env python3
"""
MCP arxiv-mcp-server接続テストスクリプト

使用方法:
    python scripts/test_mcp_connection.py

環境変数:
    ARXIV_MCP_ENABLE=true
    ARXIV_MCP_CMD=uv
    ARXIV_MCP_ARGS="tool run arxiv-mcp-server"
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.mcp_arxiv import (
    mcp_search_papers,
    mcp_download_paper,
    mcp_list_papers,
    mcp_read_paper,
)


async def test_mcp_connection():
    """MCP接続をテストする"""
    print("🔍 MCP arxiv-mcp-server 接続テスト開始")
    print(f"ARXIV_MCP_ENABLE: {os.getenv('ARXIV_MCP_ENABLE', 'false')}")
    print(f"ARXIV_MCP_CMD: {os.getenv('ARXIV_MCP_CMD', 'uv')}")
    print(f"ARXIV_MCP_ARGS: {os.getenv('ARXIV_MCP_ARGS', 'tool run arxiv-mcp-server')}")
    print()

    # 1. 論文検索テスト
    print("1️⃣ 論文検索テスト")
    try:
        papers = await mcp_search_papers("transformer", max_results=3)
        print(f"✅ 検索成功: {len(papers)}件の論文を取得")
        for i, paper in enumerate(papers[:2], 1):
            print(f"   {i}. {paper.get('title', 'No title')[:60]}...")
    except Exception as e:
        print(f"❌ 検索失敗: {e}")
    print()

    # 2. ダウンロード済み論文リストテスト
    print("2️⃣ ダウンロード済み論文リストテスト")
    try:
        downloaded_papers = await mcp_list_papers()
        print(f"✅ リスト取得成功: {len(downloaded_papers)}件のダウンロード済み論文")
        for i, paper in enumerate(downloaded_papers[:3], 1):
            print(
                f"   {i}. {paper.get('title', paper.get('paper_id', 'Unknown'))[:60]}..."
            )
    except Exception as e:
        print(f"❌ リスト取得失敗: {e}")
    print()

    # 3. 論文ダウンロードテスト（有名な論文IDを使用）
    test_paper_id = "1706.03762"  # "Attention Is All You Need"
    print(f"3️⃣ 論文ダウンロードテスト (ID: {test_paper_id})")
    try:
        success = await mcp_download_paper(test_paper_id)
        if success:
            print("✅ ダウンロード成功")
        else:
            print("⚠️ ダウンロード失敗（既にダウンロード済みの可能性）")
    except Exception as e:
        print(f"❌ ダウンロード失敗: {e}")
    print()

    # 4. 論文読み込みテスト
    print(f"4️⃣ 論文読み込みテスト (ID: {test_paper_id})")
    try:
        content = await mcp_read_paper(test_paper_id)
        if content:
            print(f"✅ 読み込み成功: {len(content)}文字のコンテンツを取得")
            print(f"   プレビュー: {content[:200]}...")
        else:
            print("⚠️ コンテンツが空です")
    except Exception as e:
        print(f"❌ 読み込み失敗: {e}")
    print()

    print("🏁 MCP接続テスト完了")


async def main():
    """メイン関数"""
    if os.getenv("ARXIV_MCP_ENABLE", "false").lower() != "true":
        print("❌ ARXIV_MCP_ENABLE=true を設定してください")
        print("例: export ARXIV_MCP_ENABLE=true")
        return

    try:
        await test_mcp_connection()
    except KeyboardInterrupt:
        print("\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
