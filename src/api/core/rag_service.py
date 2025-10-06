"""RAG service for answering questions using the index."""

from typing import Dict, Any
from pipelines.corrective import answer_with_correction
from retrieval.inmemory import InMemoryIndex


def answer_question(question: str, index: InMemoryIndex) -> Dict[str, Any]:
    """
    Answer a question using the RAG index.

    Args:
        question: User question
        index: RAG index to search

    Returns:
        Dict with 'text' and 'citations' keys
    """
    try:
        # Use corrective RAG pipeline
        result = answer_with_correction(question, index=index)

        return {
            "text": result.text,
            "citations": result.citations,
            "support": result.support,
            "attempts": result.attempts,
        }
    except Exception as e:
        # Fallback to simple response
        return {
            "text": f"申し訳ございませんが、質問に回答できませんでした: {str(e)}",
            "citations": [],
            "support": 0.0,
            "attempts": [],
        }
