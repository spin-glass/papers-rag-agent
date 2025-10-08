import asyncio
import logging
from threading import RLock
from typing import List, Optional, Sequence

from src.data.cache_loader import cache_exists, load_precomputed_cache
from src.retrieval.arxiv_searcher import search_arxiv_papers
from src.retrieval.inmemory import InMemoryIndex

log = logging.getLogger(__name__)


class RagIndexHolder:
    def __init__(self) -> None:
        self._index: Optional[InMemoryIndex] = None
        self._lock = RLock()

    def get(self) -> Optional[InMemoryIndex]:
        with self._lock:
            return self._index

    def set(self, idx: InMemoryIndex) -> None:
        if idx is None:
            raise ValueError("idx must not be None")
        with self._lock:
            self._index = idx

    def is_ready(self) -> bool:
        with self._lock:
            return self._index is not None

    def size(self) -> int:
        with self._lock:
            if self._index is None:
                return 0
            # InMemoryIndex 側の属性名に合わせる
            return len(self._index.papers_with_embeddings)


_DEFAULT_QUERIES = (
    "transformer attention mechanism language",
    "BERT GPT language model pre-training",
    "fine-tuning RLHF instruction following",
    "efficient transformer attention flash",
    "language model evaluation benchmark",
    "neural machine translation attention",
    "pre-trained language representation",
    "self-attention multi-head transformer",
)
_FALLBACK_QUERIES = ("transformer", "attention mechanism", "BERT", "GPT")


def load_or_build_index(
    queries: Sequence[str] = _DEFAULT_QUERIES,
    per_query: int = 8,
    fallback_queries: Sequence[str] = _FALLBACK_QUERIES,
    fallback_per_query: int = 10,
) -> InMemoryIndex:
    # 1) キャッシュ
    try:
        if cache_exists():
            log.info("📖 Loading precomputed cache...")
            idx = load_precomputed_cache()
            if idx is not None:
                log.info(
                    "✅ Loaded index from cache (papers=%d)",
                    len(idx.papers_with_embeddings),
                )
                return idx
            log.warning("⚠️ Cache returned None; fallback to dynamic build.")
        else:
            log.info("ℹ️ Precomputed cache not found; dynamic build will be used.")
    except Exception:
        log.exception("⚠️ Cache load failed; fallback to dynamic build.")

    # 2) 動的ビルド（メインクエリ）
    idx = _build_index_from_queries(queries, per_query)
    if idx is not None:
        return idx

    # 3) フォールバッククエリ
    log.warning("⚠️ Main queries yielded no unique papers; trying fallback queries...")
    idx = _build_index_from_queries(fallback_queries, fallback_per_query)
    if idx is not None:
        return idx

    # 4) 空のIndexを返す（API層で503等の判断を行う）
    log.error("❌ Failed to build index from any query set; returning empty index.")
    empty = InMemoryIndex()
    empty.build([])  # 空許容前提
    return empty


async def a_load_or_build_index(
    queries=_DEFAULT_QUERIES,
    per_query: int = 8,
    fallback_queries=_FALLBACK_QUERIES,
    fallback_per_query: int = 10,
) -> InMemoryIndex:
    return await asyncio.to_thread(
        load_or_build_index,
        queries,
        per_query,
        fallback_queries,
        fallback_per_query,
    )


def _build_index_from_queries(
    queries: Sequence[str],
    per_query: int,
) -> Optional[InMemoryIndex]:
    all_papers: List = []
    for i, q in enumerate(queries, start=1):
        try:
            batch = search_arxiv_papers(q, max_results=per_query)
            all_papers.extend(batch)
            log.info(
                "🔎 Query %d/%d '%s' -> %d papers",
                i,
                len(queries),
                q,
                len(batch),
            )
        except Exception:
            log.exception("  ❌ Query failed: %s", q)

    # 重複排除（Paperオブジェクトが .id を持つ前提）
    seen_ids = set()
    unique = []
    for p in all_papers:
        pid = getattr(p, "id", None)
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique.append(p)

    if not unique:
        return None

    idx = InMemoryIndex()
    idx.build(unique)  # 内部で埋め込みなどを構築する想定
    log.info(
        "✅ Built InMemoryIndex (papers=%d, embedded=%d)",
        len(unique),
        len(idx.papers_with_embeddings),
    )
    return idx
