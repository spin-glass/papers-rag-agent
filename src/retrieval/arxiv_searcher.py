import urllib.parse
import feedparser
from typing import List, Dict

ARXIV_API = "https://export.arxiv.org/api/query"


def run_arxiv_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """arXivを検索して {id,title,link,pdf} のdictリストを返す"""
    # TODO: 戻り値を List[Paper]（src/models.py の Pydantic）に変更し、score/metadata/updated を拡張。UI側は dict参照→属性参照へ切替える。
    q = f"all:{query}"  # TODO: LLMでカテゴリ/期間を補完（prompts.py, schemas.py を追加）→ search_query に cat: を付与、URLに submittedDate=YYYYMMDD+TO+YYYYMMDD を追加。失敗時はフォールバック。
    url = (
        f"{ARXIV_API}?search_query={urllib.parse.quote(q)}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    for e in getattr(feed, "entries", []):
        pdf = ""
        for link in getattr(e, "links", []):
            if getattr(link, "type", "") == "application/pdf":
                pdf = getattr(link, "href", "")
                break
        arxiv_id_core = (
            e.id.split("/")[-1].split("v")[0] if getattr(e, "id", "") else ""
        )
        results.append(
            {
                "id": arxiv_id_core,
                "title": getattr(e, "title", ""),
                "link": getattr(e, "link", ""),
                "pdf": pdf,
            }
        )
    return results
