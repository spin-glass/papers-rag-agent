import logging
from fastapi import APIRouter, Depends, HTTPException
from api.deps import get_index_holder
from api.schema import InitIndexRequest, InitIndexResponse
from api.core.rag_index import a_load_or_build_index

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/admin/init-index", response_model=InitIndexResponse)
async def init_index(_: InitIndexRequest, holder=Depends(get_index_holder)):
    try:
        idx = await a_load_or_build_index()
        holder.set(idx)
        size = holder.size()
        log.info("index rebuilt (size=%d)", size)
        return InitIndexResponse(ok=True, size=size)
    except Exception as e:
        log.exception("init-index failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
