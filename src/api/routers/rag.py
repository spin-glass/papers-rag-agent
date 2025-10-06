import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.deps import get_index_holder
from api.schema import AskRequest, AskResponse
from api.core.rag_service import answer_question
from api.core.graph_service import stream_message

router = APIRouter()


@router.post("/rag/ask", response_model=AskResponse)
async def rag_ask(req: AskRequest, holder=Depends(get_index_holder)):
    if not holder.is_ready():
        raise HTTPException(status_code=503, detail="RAG index not ready")
    ans = await asyncio.to_thread(answer_question, req.query, holder.get())
    return AskResponse(
        ok=True, answer=ans.get("text", ""), citations=ans.get("citations")
    )


@router.post("/rag/stream")
async def rag_stream(req: AskRequest, holder=Depends(get_index_holder)):
    if not holder.is_ready():
        raise HTTPException(status_code=503, detail="RAG index not ready")

    async def event_gen():
        async for chunk in stream_message(req.query, holder.get()):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)
        yield "data: [DONE]\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Content-Type": "text/event-stream; charset=utf-8",
        "Connection": "keep-alive",
    }
    return StreamingResponse(
        event_gen(), headers=headers, media_type="text/event-stream"
    )
