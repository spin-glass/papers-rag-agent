"""Configuration management for Papers RAG Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return api_key


def get_llm_provider() -> str:
    """Get LLM provider name."""
    return os.getenv("LLM_PROVIDER", "openai")


def get_top_k() -> int:
    """Get TOP_K parameter for retrieval."""
    return int(os.getenv("TOP_K", "5"))


def get_support_threshold() -> float:
    """Get support threshold for corrective RAG."""
    return float(os.getenv("SUPPORT_THRESHOLD", "0.62"))


def get_max_output_chars() -> int:
    """Get maximum output characters for chunked sending."""
    return int(os.getenv("MAX_OUTPUT_CHARS", "1400"))


def use_langgraph() -> bool:
    """Check if LangGraph workflows should be used."""
    return os.getenv("USE_LANGGRAPH", "false").lower() == "true"


def get_graph_recursion_limit() -> int:
    """Get recursion limit for LangGraph workflows."""
    return int(os.getenv("GRAPH_RECURSION_LIMIT", "10"))
