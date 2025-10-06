from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_index_holder
from api.core.rag_index import a_load_or_build_index

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
log = logging.getLogger("papers-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    holder = get_index_holder()
    log.info("Initializing RAG index…")
    try:
        idx = await a_load_or_build_index()
        holder.set(idx)
        log.info("✅ index ready (size=%d)", holder.size())
    except Exception as e:
        log.exception("❌ index init failed: %s", e)
    yield


app = FastAPI(title="Papers API", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.run.app",  # Cloud Runのデフォルトドメイン
        "https://*.googleusercontent.com",  # Cloud Runのカスタムドメイン
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ルーター
from api.routers import health, admin, arxiv, rag  # noqa: E402

app.include_router(health.router, tags=["Health"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(arxiv.router, tags=["Arxiv"])
app.include_router(rag.router, tags=["RAG"])
