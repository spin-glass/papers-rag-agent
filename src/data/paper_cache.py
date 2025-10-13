from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

STORAGE_PATH = os.getenv(
    "ARXIV_STORAGE_PATH", os.path.expanduser("~/.arxiv-mcp-server/papers")
)
CACHE_DIR = Path(STORAGE_PATH) / "cache"
TTL_DAYS = int(os.getenv("ARXIV_CACHE_TTL_DAYS", "7"))


def _cache_file(arxiv_id: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{arxiv_id}.json"


def get_cached(arxiv_id: str) -> Optional[dict]:
    cache_path = _cache_file(arxiv_id)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if not is_fresh(payload):
            return None

        return payload
    except (json.JSONDecodeError, KeyError):
        return None


def set_cached(arxiv_id: str, payload: dict) -> None:
    cache_path = _cache_file(arxiv_id)
    payload["updated_at"] = datetime.utcnow().isoformat()

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def is_fresh(payload: dict) -> bool:
    if "updated_at" not in payload:
        return False

    try:
        updated_at = datetime.fromisoformat(payload["updated_at"])
        age = datetime.utcnow() - updated_at
        return age < timedelta(days=TTL_DAYS)
    except (ValueError, TypeError):
        return False
