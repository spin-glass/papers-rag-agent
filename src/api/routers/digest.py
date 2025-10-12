from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncio
from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.retrieval.arxiv_searcher import search_arxiv_papers
from src.api.utils.persona import (
    filter_papers,
    exclude_only,
    make_short_summary,
    translate_to_japanese,
    get_min_results_threshold,
)
from src.models import Paper


router = APIRouter()


class DigestItem(BaseModel):
    id: str
    title: str
    url: str
    pdf: Optional[str] = None
    summary_short: Optional[str] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None


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
    return items
