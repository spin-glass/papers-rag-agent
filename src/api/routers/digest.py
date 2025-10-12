from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.retrieval.arxiv_searcher import search_arxiv_papers
from src.api.utils.persona import (
    filter_papers,
    exclude_only,
    make_short_summary,
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
    date_range = _date_range_for_last_days(days)
    fetch_n = min(200, max(limit * 4, limit))
    papers: List[Paper] = search_arxiv_papers(
        query=f"cat:{cat}", max_results=fetch_n, date_range=date_range
    )

    filtered = filter_papers(papers)
    min_n = get_min_results_threshold()
    if len(filtered) == 0:
        filtered = exclude_only(papers)
    elif len(filtered) < min_n:
        filtered = exclude_only(papers)
    top = filtered[:limit]

    items: List[DigestItem] = []
    for p in top:
        items.append(
            DigestItem(
                id=p.id,
                title=p.title,
                url=p.link,
                pdf=p.pdf,
                summary_short=make_short_summary(p.summary or ""),
                categories=p.categories,
                authors=p.authors,
            )
        )
    return items
