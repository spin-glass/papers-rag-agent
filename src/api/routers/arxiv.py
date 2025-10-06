from fastapi import APIRouter, HTTPException
from api.schema import ArxivSearchRequest, ArxivSearchResponse, Paper
from api.core.arxiv_service import search

router = APIRouter()


@router.post("/arxiv/search", response_model=ArxivSearchResponse)
async def arxiv_search(req: ArxivSearchRequest):
    try:
        results = await search(req.query, req.max_results)  # list[dict]
        items = [
            Paper(
                **{
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "summary": r.get("summary"),
                    "authors": r.get("authors"),
                }
            )
            for r in results
        ]
        return ArxivSearchResponse(ok=True, count=len(items), items=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
