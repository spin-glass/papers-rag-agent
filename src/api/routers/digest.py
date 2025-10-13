from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncio
import os
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from src.retrieval.arxiv_searcher import search_arxiv_papers
from src.api.utils.persona import (
    filter_papers,
    exclude_only,
    make_short_summary,
    translate_to_japanese,
    get_min_results_threshold,
)
from src.models import Paper, CornellNote, QuizItem, Citation
from src.data.paper_cache import get_cached, set_cached
from src.integrations.mcp_arxiv import (
    MCPArxivError,
    compute_hash,
    mcp_download_paper,
    mcp_read_paper,
)
from src.retrieval.sections import build_sections


def _generate_paper_structure(title: str, summary: str, rag_results: list) -> dict:
    """
    論文の構造を生成し、サボっていないかをチェックする

    Args:
        title: 論文タイトル
        summary: 論文要約
        rag_results: RAG処理結果のリスト

    Returns:
        論文構造の辞書
    """
    structure: dict = {
        "sections": [],
        "content_quality": "high",
        "analysis_completeness": "complete",
    }

    # RAG結果から論文の章立てを抽出
    for result in rag_results:
        try:
            if hasattr(result, "text") and result.text and len(result.text) > 100:
                # 論文の章立てを抽出
                sections = _extract_paper_sections(result.text)
                structure["sections"].extend(sections)
        except Exception as e:
            print(f"⚠️ Error processing RAG result: {e}")
            continue

    # 重複を除去
    structure["sections"] = list(set(structure["sections"]))

    # サボっていないかをチェック
    if len(structure["sections"]) < 3:
        structure["content_quality"] = "low"
        structure["analysis_completeness"] = "incomplete"

    return structure


def _extract_paper_sections(text: str) -> List[str]:
    """
    テキストから論文の章立てを抽出する

    Args:
        text: RAG結果のテキスト

    Returns:
        章立てのリスト
    """
    try:
        sections = []

        # 一般的な章立てパターンを検索
        section_patterns = [
            "Abstract",
            "Introduction",
            "Related Work",
            "Methodology",
            "Method",
            "Approach",
            "Experiments",
            "Results",
            "Discussion",
            "Conclusion",
            "Future Work",
            "Acknowledgments",
            "References",
        ]

        for pattern in section_patterns:
            if pattern.lower() in text.lower():
                sections.append(pattern)

        return sections
    except Exception as e:
        print(f"⚠️ Section extraction failed: {e}")
        return []


router = APIRouter()


class DigestItem(BaseModel):
    id: str
    title: str
    url: str
    pdf: Optional[str] = None
    summary_short: Optional[str] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None


class DigestDetails(BaseModel):
    """詳細表示用のデータモデル"""

    paper_id: str
    title: str
    url: str
    pdf: Optional[str] = None
    full_summary: Optional[str] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    cornell_note: Optional[CornellNote] = None
    quiz_items: Optional[List[QuizItem]] = None
    citations: Optional[List[Citation]] = None
    paper_structure: Optional[dict] = None
    sections: Optional[List[dict]] = None
    toc_flat: Optional[List[str]] = None
    content_length: Optional[int] = None
    content_hash: Optional[str] = None
    has_full_text: bool = False


def _date_range_for_last_days(days: int) -> str:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, days))
    fr = start.strftime("%Y%m%d") + "*"
    to = now.strftime("%Y%m%d") + "*"
    return f"{fr} TO {to}"


@router.get("/digest", response_model=List[DigestItem])
async def get_digest(
    cat: str = Query(default="cs.LG", description="arXiv category, e.g., cs.LG"),
    days: int = Query(default=2, ge=1, le=7),
    limit: int = Query(default=10, ge=1, le=50),
):
    cur_days = days
    filtered: List[Paper] = []
    min_n = get_min_results_threshold()

    while True:
        date_range = _date_range_for_last_days(cur_days)
        fetch_n = min(200, max(limit * 4, limit))
        papers: List[Paper] = search_arxiv_papers(
            query=f"cat:{cat}", max_results=fetch_n, date_range=date_range
        )

        filtered = filter_papers(papers)
        if len(filtered) == 0 or len(filtered) < min_n:
            filtered = exclude_only(papers)

        if filtered or cur_days >= 7:
            break
        cur_days += 1

    top = filtered[:limit]

    # 並列で翻訳処理を実行
    async def translate_paper(p):
        title_task = asyncio.create_task(
            asyncio.to_thread(translate_to_japanese, p.title, 200)
        )
        summary_task = asyncio.create_task(
            asyncio.to_thread(make_short_summary, p.summary or "")
        )

        translated_title, translated_summary = await asyncio.gather(
            title_task, summary_task
        )

        return DigestItem(
            id=p.id,
            title=translated_title,
            url=p.link,
            pdf=p.pdf,
            summary_short=translated_summary,
            categories=p.categories,
            authors=p.authors,
        )

    # 全ての論文を並列で翻訳
    items = await asyncio.gather(*[translate_paper(p) for p in top])

    prefetch_k = int(os.getenv("ARXIV_PREFETCH_TOPK", "10"))
    topk = min(prefetch_k, len(top))

    async def prefetch_paper(paper: Paper) -> None:
        try:
            cached = get_cached(paper.id)
            if cached:
                return

            success = await mcp_download_paper(paper.id)
            if not success:
                return

            content = await mcp_read_paper(paper.id, fmt="plain")
            if not content:
                return

            sections_data = build_sections(content)
            payload = {
                "content": content,
                "content_hash": compute_hash(content),
                "content_length": len(content),
                "sections": sections_data["sections"],
                "toc_flat": sections_data["toc_flat"],
                "format": "plain",
            }
            set_cached(paper.id, payload)
        except Exception:
            pass

    for i in range(topk):
        asyncio.create_task(prefetch_paper(top[i]))

    return items


@router.get("/digest/{paper_id}/details", response_model=DigestDetails)
async def get_digest_details(paper_id: str):
    """
    特定の論文の詳細情報を取得するエンドポイント

    Args:
        paper_id: 論文のID（arXiv ID）

    Returns:
        DigestDetails: 論文の詳細情報
    """
    try:
        # 論文の基本情報を取得（arXiv IDを直接検索）
        # 直接arXiv APIを呼び出して検索
        import feedparser

        url = f"https://export.arxiv.org/api/query?search_query=id:{paper_id}&max_results=1"
        feed = feedparser.parse(url)
        papers = []

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

        if not papers:
            raise HTTPException(
                status_code=404, detail=f"Paper with ID {paper_id} not found"
            )

        paper = papers[0]

        # 翻訳処理を並列実行
        title_task = asyncio.create_task(
            asyncio.to_thread(translate_to_japanese, paper.title, 200)
        )
        summary_task = asyncio.create_task(
            asyncio.to_thread(translate_to_japanese, paper.summary or "", 1000)
        )

        translated_title, translated_summary = await asyncio.gather(
            title_task, summary_task
        )

        # RAG結果からCornell Note、Quiz、Citationsを取得
        cornell_note = None
        quiz_items = None
        citations = None
        paper_structure = None

        try:
            # 論文の構造分析用の質問を複数実行
            questions = [
                f"{translated_title}の論文構造と章立てについて詳しく教えてください",
                f"{translated_title}の研究方法と実験について詳しく教えてください",
                f"{translated_title}の結果と結論について詳しく教えてください",
            ]

            # RAG indexを取得
            from src.api.deps import get_index_holder

            index_holder = get_index_holder()
            index = index_holder.get() if index_holder else None
            if index:
                # RAG処理を実行
                from src.graphs.corrective_rag import answer_with_correction_graph
                from src.graphs.content_enhancement import enhance_answer_content

                # 複数の質問でRAG処理を実行
                rag_results = []
                for question in questions:
                    try:
                        basic_result = answer_with_correction_graph(
                            question, index=index
                        )
                        enhanced_result = enhance_answer_content(basic_result, question)
                        rag_results.append(enhanced_result)
                    except Exception as e:
                        print(
                            f"⚠️ RAG processing failed for question: {question[:50]}... - {e}"
                        )
                        continue

                # 結果を統合
                if rag_results:
                    # 最新の結果を使用
                    latest_result = rag_results[-1]
                    cornell_note = latest_result.cornell_note
                    quiz_items = latest_result.quiz_items

                    # Citationsを適切な形式に変換
                    citations = []
                    if latest_result.citations:
                        for citation_dict in latest_result.citations:
                            try:
                                # RAG結果のcitation形式に合わせて変換
                                citation = Citation(
                                    title=citation_dict.get("title", ""),
                                    url=citation_dict.get("url")
                                    or citation_dict.get("link", ""),
                                    id=citation_dict.get("id"),
                                    authors=citation_dict.get("authors"),
                                    year=citation_dict.get("year"),
                                )
                                citations.append(citation)
                            except Exception as e:
                                print(f"⚠️ Citation conversion failed: {e}")
                                continue

                    # 論文構造を生成
                    paper_structure = _generate_paper_structure(
                        translated_title, translated_summary, rag_results
                    )

        except Exception as e:
            print(f"⚠️ RAG enhancement failed for paper {paper_id}: {e}")
            # RAG処理が失敗した場合は基本的な情報のみ提供

        # 詳細情報を構築
        try:
            sections = None
            toc_flat = None
            content_length = None
            content_hash = None
            has_full_text = False

            try:
                cached = get_cached(paper.id)
                if not cached:
                    success = await mcp_download_paper(paper.id)
                    if success:
                        content = await mcp_read_paper(paper.id, fmt="plain")
                        if content:
                            sections_data = build_sections(content)
                            payload = {
                                "content": content,
                                "content_hash": compute_hash(content),
                                "content_length": len(content),
                                "sections": sections_data["sections"],
                                "toc_flat": sections_data["toc_flat"],
                                "format": "plain",
                            }
                            set_cached(paper.id, payload)
                            cached = payload

                if cached:
                    sections = cached.get("sections")
                    toc_flat = cached.get("toc_flat")
                    content_length = cached.get("content_length")
                    content_hash = cached.get("content_hash")
                    has_full_text = bool(content_length and content_length > 0)
            except (MCPArxivError, Exception):
                pass

            details = DigestDetails(
                paper_id=paper.id,
                title=translated_title,
                url=paper.link,
                pdf=paper.pdf,
                full_summary=translated_summary,
                categories=paper.categories,
                authors=paper.authors,
                cornell_note=cornell_note,
                quiz_items=quiz_items,
                citations=citations,
                paper_structure=paper_structure,
                sections=sections,
                toc_flat=toc_flat,
                content_length=content_length,
                content_hash=content_hash,
                has_full_text=has_full_text,
            )

            return details
        except Exception as e:
            print(f"❌ Failed to create DigestDetails: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create paper details: {str(e)}"
            )

    except Exception as e:
        print(f"❌ Failed to get paper details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get paper details: {str(e)}"
        )


@router.get("/digest/{paper_id}/fulltext")
async def get_fulltext(
    paper_id: str,
    format: str = Query(default="plain", pattern="^(plain|md)$"),
    max_bytes: int = Query(default=200000, ge=1000, le=10000000),
) -> PlainTextResponse:
    """論文の全文コンテンツを取得"""
    try:
        cached = get_cached(paper_id)
        content = None

        if cached and cached.get("format") == format and "content" in cached:
            content = cached["content"]

        if content is None:
            success = await mcp_download_paper(paper_id)
            if not success:
                raise HTTPException(
                    status_code=404, detail=f"Could not download paper {paper_id}"
                )

            content = await mcp_read_paper(paper_id, fmt=format)
            if not content:
                raise HTTPException(
                    status_code=404, detail=f"Could not read paper {paper_id}"
                )

            existing_cache = get_cached(paper_id)
            if existing_cache:
                existing_cache["content"] = content
                existing_cache["format"] = format
                set_cached(paper_id, existing_cache)
            else:
                sections_data = build_sections(content)
                payload = {
                    "content": content,
                    "content_hash": compute_hash(content),
                    "content_length": len(content),
                    "sections": sections_data["sections"],
                    "toc_flat": sections_data["toc_flat"],
                    "format": format,
                }
                set_cached(paper_id, payload)

        data = content[:max_bytes] if isinstance(content, str) else ""

        return PlainTextResponse(data, media_type="text/plain; charset=utf-8")

    except HTTPException:
        raise
    except MCPArxivError as e:
        raise HTTPException(
            status_code=503, detail=f"MCP service error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
