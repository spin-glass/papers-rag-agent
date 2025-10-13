"""
Direct arXiv integration as fallback for MCP
MCPが利用できない環境での代替実装
"""

from __future__ import annotations

import aiohttp
import feedparser
from typing import List, Dict, Any
import os
from pathlib import Path


class ArxivDirectError(Exception):
    pass


async def direct_search_papers(
    query: str,
    max_results: int = 10,
    date_from: str | None = None,
    categories: list | None = None,
) -> List[Dict[str, Any]]:
    """arXiv APIを直接使用した論文検索"""
    try:
        # arXiv API URL構築
        base_url = "http://export.arxiv.org/api/query"

        # クエリパラメータ構築
        search_query = query
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            search_query = f"({search_query}) AND ({cat_query})"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                content = await response.text()

        # feedparserで解析
        feed = feedparser.parse(content)

        papers = []
        for entry in feed.entries:
            # arXiv IDを抽出
            arxiv_id = entry.id.split("/")[-1].split("v")[0]

            # 著者リスト
            authors = [author.name for author in getattr(entry, "authors", [])]

            # カテゴリリスト
            categories = [tag.term for tag in getattr(entry, "tags", [])]

            paper = {
                "id": arxiv_id,
                "title": entry.title,
                "authors": authors,
                "abstract": entry.summary,
                "categories": categories,
                "published": entry.published,
                "url": f"http://arxiv.org/pdf/{arxiv_id}",
                "resource_uri": f"arxiv://{arxiv_id}",
            }
            papers.append(paper)

        return papers

    except Exception as e:
        raise ArxivDirectError(f"Direct arXiv search failed: {e}")


async def direct_download_paper(arxiv_id: str) -> bool:
    """論文PDFの直接ダウンロード（簡易版）"""
    try:
        storage_path = Path(os.getenv("ARXIV_STORAGE_PATH", "/tmp/arxiv-papers"))
        storage_path.mkdir(parents=True, exist_ok=True)

        pdf_path = storage_path / f"{arxiv_id}.pdf"

        # 既にダウンロード済みの場合
        if pdf_path.exists():
            return True

        # PDF URLからダウンロード
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(pdf_path, "wb") as f:
                        f.write(content)
                    return True
                else:
                    return False

    except Exception:
        return False


async def direct_list_papers() -> List[Dict[str, Any]]:
    """ダウンロード済み論文のリスト取得"""
    try:
        storage_path = Path(os.getenv("ARXIV_STORAGE_PATH", "/tmp/arxiv-papers"))

        if not storage_path.exists():
            return []

        papers = []
        for pdf_file in storage_path.glob("*.pdf"):
            arxiv_id = pdf_file.stem
            papers.append(
                {
                    "id": arxiv_id,
                    "title": f"Paper {arxiv_id}",
                    "local_path": str(pdf_file),
                }
            )

        return papers

    except Exception:
        return []


async def direct_read_paper(arxiv_id: str) -> str:
    """論文内容の読み込み（テキスト抽出）"""
    try:
        storage_path = Path(os.getenv("ARXIV_STORAGE_PATH", "/tmp/arxiv-papers"))
        pdf_path = storage_path / f"{arxiv_id}.pdf"

        if not pdf_path.exists():
            # ダウンロードを試行
            if not await direct_download_paper(arxiv_id):
                return ""

        # 簡易的なテキスト抽出（実際にはPDF解析ライブラリが必要）
        return f"Paper content for {arxiv_id} (PDF text extraction not implemented in fallback mode)"

    except Exception:
        return ""
