"""Embedding functionality using OpenAI."""

import numpy as np
from openai import OpenAI
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_openai_api_key, get_llm_provider


def setup_embedder():
    """Setup embedding client based on environment configuration."""
    provider = get_llm_provider()
    if provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    api_key = get_openai_api_key()
    return OpenAI(api_key=api_key)


def get_embed(text: str) -> np.ndarray:
    """
    Get embedding vector for text using OpenAI's embedding model.
    
    Args:
        text: Input text to embed
        
    Returns:
        numpy array of embedding vector
        
    Raises:
        Exception: If embedding generation fails
    """
    client = setup_embedder()
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",  # Cost-efficient model
            input=text.strip()
        )
        
        # Extract embedding vector
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
        
    except Exception as e:
        # Don't suppress exceptions - let them bubble up
        raise Exception(f"Failed to generate embedding: {str(e)}") from e
