import urllib.parse
import feedparser
from typing import List, Dict

from src.models import Paper

ARXIV_API = "https://export.arxiv.org/api/query"


def build_improved_query(query: str) -> str:
    """
    改善されたarXiv検索クエリを構築する。

    タイトルまたはアブストラクトに検索語が含まれる論文を検索し、
    関連するカテゴリも含める。
    """
    query_lower = query.lower()

    # 特定キーワードに対する特化クエリ
    keyword_queries = {
        "transformer": "ti:transformer OR ti:attention OR abs:transformer OR (cat:cs.CL AND (transformer OR attention))",
        "attention": "ti:attention OR abs:attention OR (cat:cs.CL AND attention)",
        "bert": "ti:BERT OR abs:BERT OR (cat:cs.CL AND BERT)",
        "gpt": "ti:GPT OR abs:GPT OR (cat:cs.CL AND GPT)",
        "neural network": 'ti:"neural network" OR abs:"neural network" OR (cat:cs.LG AND "neural network")',
        "machine learning": "cat:cs.LG OR cat:stat.ML",
        "deep learning": 'ti:"deep learning" OR abs:"deep learning" OR (cat:cs.LG AND "deep learning")',
        "computer vision": "cat:cs.CV",
        "reinforcement learning": 'ti:"reinforcement learning" OR abs:"reinforcement learning" OR (cat:cs.LG AND "reinforcement learning")',
    }

    # 特定キーワードに一致する場合は専用クエリを使用
    for keyword, specialized_query in keyword_queries.items():
        if keyword in query_lower:
            return specialized_query

    # デフォルト：タイトルまたはアブストラクトで検索
    return f"ti:{query} OR abs:{query}"


def run_arxiv_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """arXivを検索して {id,title,link,pdf} のdictリストを返す"""
    # TODO: 戻り値を List[Paper]（src/models.py の Pydantic）に変更し、score/metadata/updated を拡張。UI側は dict参照→属性参照へ切替える。

    # 改善されたクエリ構築：タイトル、アブストラクト、カテゴリを対象とする
    q = build_improved_query(query)

    url = (
        f"{ARXIV_API}?search_query={urllib.parse.quote(q)}"
        f"&sortBy=relevance&sortOrder=descending&max_results={max_results}"
    )
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    for e in getattr(feed, "entries", []):
        pdf = ""
        for link in getattr(e, "links", []):
            if getattr(link, "type", "") == "application/pdf":
                pdf = getattr(link, "href", "")
                break
        arxiv_id_core = (
            e.id.split("/")[-1].split("v")[0] if getattr(e, "id", "") else ""
        )
        results.append(
            {
                "id": arxiv_id_core,
                "title": getattr(e, "title", ""),
                "link": getattr(e, "link", ""),
                "pdf": pdf,
            }
        )
    return results


def search_arxiv_papers(
    query: str, max_results: int = 5, date_range: str = None
) -> List[Paper]:
    """
    Search arXiv and return Paper objects with full metadata including summary.

    Args:
        query: Search query
        max_results: Maximum number of results
        date_range: Optional date range like "20170101+TO+20251231"

    Returns:
        List of Paper objects with summary field populated
    """
    q = build_improved_query(query)

    # Add date range if specified (format: "2017* TO 2025*")
    if date_range:
        q = f"({q}) AND submittedDate:[{date_range}]"

    url = (
        f"{ARXIV_API}?search_query={urllib.parse.quote(q)}"
        f"&sortBy=relevance&sortOrder=descending&max_results={max_results}"
    )

    feed = feedparser.parse(url)
    papers: List[Paper] = []

    for e in getattr(feed, "entries", []):
        # Extract PDF link
        pdf = ""
        for link in getattr(e, "links", []):
            if getattr(link, "type", "") == "application/pdf":
                pdf = getattr(link, "href", "")
                break

        # Extract arXiv ID
        arxiv_id_core = (
            e.id.split("/")[-1].split("v")[0] if getattr(e, "id", "") else ""
        )

        # Extract authors
        authors = []
        if hasattr(e, "authors"):
            authors = [getattr(author, "name", "") for author in e.authors]

        # Extract categories
        categories = []
        if hasattr(e, "tags"):
            categories = [getattr(tag, "term", "") for tag in e.tags]

        # Create Paper object
        paper = Paper(
            id=arxiv_id_core,
            title=getattr(e, "title", "").strip(),
            link=getattr(e, "link", ""),
            pdf=pdf if pdf else None,
            summary=getattr(e, "summary", "").strip(),
            authors=authors if authors else None,
            updated=getattr(e, "updated", None),
            categories=categories if categories else None,
        )

        papers.append(paper)

    return papers
