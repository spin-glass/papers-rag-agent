import os
import re
from typing import List
from src.models import Paper
from src.llm.generator import generate_answer


def _csv_env(name: str) -> List[str]:
    v = os.getenv(name, "")
    return [s.strip() for s in v.split(",") if s.strip()]


DEFAULT_INCLUDE = [
    "rag",
    "graph rag",
    "graphrag",
    "corrective",
    "retrieval",
    "re-rank",
    "rerank",
    "imrad",
    "hyde",
    "langgraph",
    "agent",
    "planner",
    "executor",
    "tool",
    "routing",
    "guardrail",
    "eval",
    "ragas",
    "langsmith",
    "test-time reasoning",
    "ttr",
    "moe",
    "distillation",
    "reasoning compression",
    "cost",
    "quality",
    "mlops",
    "vertex ai",
    "bigquery",
    "cloud run",
    "unlearning",
    "safety",
]
DEFAULT_EXCLUDE = [
    "medical",
    "healthcare",
    "clinical",
    "materials",
    "iot",
    "biology",
    "chemistry",
    "bio",
    "medicine",
]


def get_keywords():
    inc = _csv_env("PREFER_KEYWORDS_INCLUDE") or DEFAULT_INCLUDE
    exc = _csv_env("PREFER_KEYWORDS_EXCLUDE") or DEFAULT_EXCLUDE
    return [s.lower() for s in inc], [s.lower() for s in exc]


def translate_to_japanese(text: str, max_chars: int = 300) -> str:
    """英語のテキストを日本語に翻訳する"""
    if not text or not text.strip():
        return ""

    try:
        prompt = f"""以下の英語のテキストを日本語に翻訳してください。技術的な内容は正確に保ち、自然な日本語で表現してください。

{text}

翻訳:"""

        translated = generate_answer(prompt)

        # 翻訳結果が長すぎる場合は切り詰め
        if len(translated) > max_chars:
            translated = translated[:max_chars] + "..."

        return translated
    except Exception:
        # 翻訳に失敗した場合は元のテキストを返す
        return text[:max_chars] + ("..." if len(text) > max_chars else "")


def make_short_summary(text: str, max_chars: int = 300) -> str:
    t = (text or "").strip()
    if not t:
        return ""

    # まず元のテキストを短縮
    parts = re.split(r"(?<=[.!?])\s+", t)
    s = " ".join(parts[:2]) if parts else t
    if len(s) > max_chars:
        s = s[:max_chars] + "..."

    # 日本語に翻訳
    return translate_to_japanese(s, max_chars)


def filter_papers(papers: List[Paper]) -> List[Paper]:
    inc, exc = get_keywords()
    out: List[Paper] = []
    for p in papers:
        blob = f"{p.title}\n{p.summary}".lower()
        if any(x in blob for x in exc):
            continue
        if any(x in blob for x in inc):
            out.append(p)
    return out


def exclude_only(papers: List[Paper]) -> List[Paper]:
    _, exc = get_keywords()
    out: List[Paper] = []
    for p in papers:
        blob = f"{p.title}\n{p.summary}".lower()
        if any(x in blob for x in exc):
            continue
        out.append(p)
    return out


def get_min_results_threshold(default: int = 3) -> int:
    try:
        v = int(os.getenv("DIGEST_MIN_RESULTS", str(default)))
        return max(1, min(10, v))
    except Exception:
        return default
