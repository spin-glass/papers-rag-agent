"""Baseline RAG pipeline implementation."""


import numpy as np
from typing import List
from models import AnswerResult, RetrievedContext
from llm.generator import generate_answer
from llm.embeddings import get_embed
from retrieval.inmemory import InMemoryIndex
from config import get_top_k


# Global index instance - will be initialized when needed
_global_index = None


def set_global_index(index: InMemoryIndex) -> None:
    """Set the global index for baseline RAG."""
    global _global_index
    _global_index = index


def baseline_answer(question: str, index: InMemoryIndex = None) -> AnswerResult:
    """
    Generate answer using baseline RAG pipeline.

    Args:
        question: User question
        index: Optional index to use (uses global if not provided)

    Returns:
        AnswerResult with answer, citations, support score, and attempts
    """
    global _global_index

    # Use provided index or fall back to global
    search_index = index if index is not None else _global_index

    if search_index is None:
        raise ValueError(
            "No index provided and global index not initialized. Call set_global_index() first."
        )

    # 1. Retrieve contexts
    top_k = get_top_k()
    contexts = search_index.search(question, top_k)

    if not contexts:
        return AnswerResult(
            text="申し訳ございませんが、関連する論文が見つかりませんでした。",
            citations=[],
            support=0.0,
            attempts=[{"type": "baseline", "top_ids": [], "support": 0.0}],
        )

    # 2. Build prompt with contexts
    prompt = _build_baseline_prompt(question, contexts)

    # 3. Generate answer using retrieved contexts
    try:
        answer_text = generate_answer(prompt, question)
    except Exception as e:
        return AnswerResult(
            text=f"回答の生成中にエラーが発生しました: {str(e)}",
            citations=[],
            support=0.0,
            attempts=[
                {
                    "type": "baseline",
                    "top_ids": [ctx.paper_id for ctx in contexts],
                    "support": 0.0,
                }
            ],
        )

    # 4. Calculate support score
    support_score = calculate_support(question, contexts)

    # 5. Generate citations
    citations = generate_citations(contexts)

    # 6. Record attempt
    attempt = {
        "type": "baseline",
        "top_ids": [ctx.paper_id for ctx in contexts],
        "support": support_score,
    }

    return AnswerResult(
        text=answer_text, citations=citations, support=support_score, attempts=[attempt]
    )


def calculate_support(question: str, contexts: List[RetrievedContext]) -> float:
    """
    Calculate support score using cosine similarity between query and contexts.

    Args:
        question: Original question
        contexts: Retrieved contexts with embeddings

    Returns:
        Support score (0-1)
    """
    if not contexts:
        return 0.0

    try:
        # Get question embedding
        question_embedding = get_embed(question)

        # Calculate max cosine similarity with used contexts
        max_similarity = 0.0
        for ctx in contexts:
            if hasattr(ctx, "embedding") and ctx.embedding is not None:
                # Calculate cosine similarity
                q_norm = question_embedding / (
                    np.linalg.norm(question_embedding) + 1e-8
                )
                ctx_norm = ctx.embedding / (np.linalg.norm(ctx.embedding) + 1e-8)
                similarity = np.dot(q_norm, ctx_norm)
                max_similarity = max(max_similarity, float(similarity))

        return max(0.0, min(1.0, max_similarity))  # Clamp to [0, 1]

    except Exception as e:
        print(f"Warning: Failed to calculate support score: {e}")
        return 0.0


def generate_citations(contexts: List[RetrievedContext]) -> List[dict]:
    """
    Generate citations from retrieved contexts.

    Args:
        contexts: Retrieved contexts

    Returns:
        List of citation dictionaries with title and link
    """
    citations = []
    seen_titles = set()

    for ctx in contexts:
        if ctx.title not in seen_titles:
            citations.append({"title": ctx.title, "link": ctx.link})
            seen_titles.add(ctx.title)

    return citations


def _build_baseline_prompt(question: str, contexts: List[RetrievedContext]) -> str:
    """
    Build prompt for baseline RAG generation.

    Args:
        question: User question
        contexts: Retrieved contexts

    Returns:
        Complete prompt string
    """
    prompt = """You are a careful scientific assistant. Use ONLY the provided contexts.
If the contexts are insufficient, say you cannot answer and list what is missing.

Question:
{question}

Contexts:
{contexts}

Requirements:
- Bullet the key points clearly.
- Cite at least 2 sources from the contexts as titles with their arXiv abstract URLs.
- Do not invent facts not supported by the contexts.

Citations:
"""

    # Format contexts
    context_text = ""
    for i, ctx in enumerate(contexts, 1):
        context_text += f"{i}) {ctx.title}\n{ctx.summary}\n\n"

    return prompt.format(question=question, contexts=context_text.strip())
