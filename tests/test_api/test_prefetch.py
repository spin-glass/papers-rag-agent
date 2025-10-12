import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.api.routers.digest import get_digest
from src.models import Paper


@pytest.fixture
def mock_papers():
    return [
        Paper(
            id=f"2301.1234{i}",
            title=f"Test Paper {i}",
            link=f"https://arxiv.org/abs/2301.1234{i}",
            pdf=f"https://arxiv.org/pdf/2301.1234{i}.pdf",
            summary=f"Summary {i}",
            authors=["Author"],
            updated="2023-01-15",
            categories=["cs.AI"],
        )
        for i in range(5)
    ]


@pytest.mark.asyncio
async def test_digest_prefetch_topk(mock_papers, monkeypatch):
    monkeypatch.setenv("ARXIV_PREFETCH_TOPK", "2")
    
    with (
        patch("src.api.routers.digest.search_arxiv_papers", return_value=mock_papers),
        patch("src.api.routers.digest.filter_papers", return_value=mock_papers),
        patch("src.api.routers.digest.translate_to_japanese", side_effect=lambda x, _: f"Translated: {x}"),
        patch("src.api.routers.digest.make_short_summary", return_value="Short summary"),
        patch("src.api.routers.digest.get_cached", return_value=None),
        patch("src.api.routers.digest.mcp_download_paper", return_value=True) as mock_download,
        patch("src.api.routers.digest.mcp_read_paper", return_value="Test content") as mock_read,
        patch("src.api.routers.digest.set_cached") as mock_set_cache,
        patch("src.api.routers.digest.build_sections", return_value={"sections": [], "toc_flat": []}),
        patch("src.api.routers.digest.compute_hash", return_value="hash123"),
    ):
        result = await get_digest(cat="cs.AI", days=1, limit=5)
        
        assert len(result) == 5


@pytest.mark.asyncio
async def test_digest_prefetch_with_cache_hit(mock_papers, monkeypatch):
    monkeypatch.setenv("ARXIV_PREFETCH_TOPK", "1")
    
    cache_payload = {
        "content": "Cached content",
        "sections": [],
        "toc_flat": [],
    }
    
    with (
        patch("src.api.routers.digest.search_arxiv_papers", return_value=mock_papers),
        patch("src.api.routers.digest.filter_papers", return_value=mock_papers),
        patch("src.api.routers.digest.translate_to_japanese", side_effect=lambda x, _: f"Translated: {x}"),
        patch("src.api.routers.digest.make_short_summary", return_value="Short summary"),
        patch("src.api.routers.digest.get_cached", return_value=cache_payload),
        patch("src.api.routers.digest.mcp_download_paper") as mock_download,
        patch("src.api.routers.digest.mcp_read_paper") as mock_read,
    ):
        result = await get_digest(cat="cs.AI", days=1, limit=5)
        
        assert len(result) == 5
