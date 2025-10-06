"""Embedding functionality using OpenAI with LangSmith tracing."""

import numpy as np
from langchain_openai import OpenAIEmbeddings
from langsmith import traceable

from src.config import get_openai_api_key, get_llm_provider


def setup_embedder():
    """Setup embedding client based on environment configuration."""
    provider = get_llm_provider()
    if provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {provider}")

    api_key = get_openai_api_key()
    return OpenAIEmbeddings(
        model="text-embedding-3-small",  # Cost-efficient model
        openai_api_key=api_key,
    )


@traceable
def get_embed(text: str) -> np.ndarray:
    """
    Get embedding vector for text using OpenAI's embedding model with LangSmith tracing.

    Args:
        text: Input text to embed

    Returns:
        numpy array of embedding vector

    Raises:
        Exception: If embedding generation fails
    """
    embeddings = setup_embedder()

    try:
        # Use LangChain's OpenAIEmbeddings for automatic LangSmith tracing
        embedding_vector = embeddings.embed_query(text.strip())
        return np.array(embedding_vector, dtype=np.float32)

    except Exception as e:
        # Don't suppress exceptions - let them bubble up
        raise Exception(f"Failed to generate embedding: {str(e)}") from e
