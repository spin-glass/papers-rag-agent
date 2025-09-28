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
        print("⚠️ OPENAI_API_KEY not found in environment variables")
        print("Please set OPENAI_API_KEY environment variable or create .env file")
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return api_key


def get_openai_api_key_safe() -> str | None:
    """Get OpenAI API key safely without raising exceptions."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY not found, some features will be disabled")
        return None
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
    try:
        limit = int(os.getenv("GRAPH_RECURSION_LIMIT", "10"))
        # Ensure the limit is reasonable (between 1 and 100)
        if limit <= 0:
            print(f"⚠️ Invalid recursion limit {limit}, using default 10")
            return 10
        elif limit > 100:
            print(f"⚠️ Recursion limit {limit} is very high, using 100")
            return 100
        return limit
    except (ValueError, TypeError):
        print("⚠️ Invalid GRAPH_RECURSION_LIMIT value, using default 10")
        return 10
