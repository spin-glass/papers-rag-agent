#!/usr/bin/env python3
"""
Build precomputed cache for RAG index.
This script generates papers and embeddings cache for fast startup.
"""

import json
import pickle
import asyncio
import os
import numpy as np
from pathlib import Path

from src.retrieval.arxiv_searcher import search_arxiv_papers
from src.retrieval.inmemory import InMemoryIndex


def _use_local_embeddings() -> bool:
    """Check if we should use local embeddings instead of calling OpenAI."""
    key = os.environ.get("OPENAI_API_KEY", "")
    ci = os.environ.get("CI", "")
    return (ci.lower() in ("1", "true")) or (not key) or (key == "test_key")


def _make_local_embedding(text: str, dim: int = 64) -> np.ndarray:
    """Generate deterministic pseudo-embedding based on text hash."""
    seed = abs(hash(text)) % (2**32)
    rng = np.random.default_rng(seed)
    vec = rng.normal(loc=0.0, scale=1.0, size=dim).astype(np.float32)
    norm = np.linalg.norm(vec) + 1e-8
    return (vec / norm).astype(np.float32)


async def build_papers_cache():
    """Build cache of papers from arXiv searches."""
    print("🔍 Building papers cache...")

    all_papers = []

    # Search queries targeting different aspects of NLP/Transformer research
    search_queries = [
        "transformer attention mechanism language",
        "BERT GPT language model pre-training",
        "fine-tuning RLHF instruction following",
        "efficient transformer attention flash",
        "language model evaluation benchmark",
        "neural machine translation attention",
        "pre-trained language representation",
        "self-attention multi-head transformer",
    ]

    for i, query in enumerate(search_queries):
        try:
            print(f"  Query {i + 1}/{len(search_queries)}: '{query}'")
            batch_papers = search_arxiv_papers(query, max_results=8)
            all_papers.extend(batch_papers)
            print(f"    → {len(batch_papers)} papers")
        except Exception as e:
            print(f"    ❌ Failed: {e}")
            continue

    # Remove duplicates based on paper ID
    seen_ids = set()
    papers = []
    for paper in all_papers:
        if paper.id not in seen_ids:
            papers.append(paper)
            seen_ids.add(paper.id)

    # If no papers found, try fallback searches
    if not papers:
        print("⚠️  No papers from specialized queries, trying fallback...")
        fallback_queries = ["transformer", "attention mechanism", "BERT", "GPT"]
        for query in fallback_queries:
            try:
                batch_papers = search_arxiv_papers(query, max_results=10)
                all_papers.extend(batch_papers)
                print(f"  Fallback '{query}' → {len(batch_papers)} papers")
                if len(batch_papers) > 0:
                    break
            except Exception as e:
                print(f"  Fallback '{query}' failed: {e}")
                continue

        # Remove duplicates again
        seen_ids = set()
        papers = []
        for paper in all_papers:
            if paper.id not in seen_ids:
                papers.append(paper)
                seen_ids.add(paper.id)

    print(f"✅ Collected {len(papers)} unique papers")
    return papers


def build_embeddings_cache(papers):
    """Build embeddings cache from papers."""
    print("🧮 Building embeddings cache...")

    if not papers:
        print("❌ No papers to process")
        return None

    index = InMemoryIndex()

    if _use_local_embeddings():
        print("⚙️  CI/test mode detected — generating local deterministic embeddings")
        index.papers_with_embeddings = []
        for p in papers:
            text = f"{p.title}\n\n{p.summary}"
            emb = _make_local_embedding(text)
            index.papers_with_embeddings.append((p, emb))
        print(f"✅ Built embeddings for {len(index.papers_with_embeddings)} papers (local)")
        return index

    index.build(papers)
    print(f"✅ Built embeddings for {len(index.papers_with_embeddings)} papers")
    return index


def save_cache(papers, index):
    """Save papers and embeddings to cache files."""
    print("💾 Saving cache files...")

    # Create data directory
    data_dir = Path(__file__).parent.parent / "src" / "data"
    data_dir.mkdir(exist_ok=True)

    # Save papers as JSON
    papers_file = data_dir / "precomputed_papers.json"
    papers_data = [paper.model_dump() for paper in papers]
    with open(papers_file, "w", encoding="utf-8") as f:
        json.dump(papers_data, f, ensure_ascii=False, indent=2)
    print(f"  📄 Papers saved to {papers_file}")

    # Save embeddings as pickle
    embeddings_file = data_dir / "precomputed_embeddings.pkl"
    with open(embeddings_file, "wb") as f:
        pickle.dump(index.papers_with_embeddings, f)
    print(f"  🧮 Embeddings saved to {embeddings_file}")

    print("✅ Cache built successfully!")
    print(f"   Papers: {len(papers)}")
    print(f"   Embeddings: {len(index.papers_with_embeddings)}")


async def main():
    """Main cache building function."""
    print("🏗️  Building precomputed cache for Papers RAG Agent")
    print("=" * 50)

    try:
        # Build papers cache
        papers = await build_papers_cache()

        if not papers:
            print("❌ Failed to collect papers")
            return

        # Build embeddings cache
        index = build_embeddings_cache(papers)

        if index is None:
            print("❌ Failed to build embeddings")
            return

        # Save caches
        save_cache(papers, index)

        print("=" * 50)
        print("🎉 Cache building completed successfully!")

    except Exception as e:
        print(f"❌ Error building cache: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
