from fastapi import APIRouter, Depends
from api.deps import get_index_holder
from api.schema import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(holder = Depends(get_index_holder)):
    ready = holder.is_ready()
    size = holder.size() if ready else 0
    return HealthResponse(ok=True, rag_ready=ready, size=size)
