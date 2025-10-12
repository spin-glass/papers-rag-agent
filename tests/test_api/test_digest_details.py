import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.routers.digest import get_digest_details
from src.models import Paper


@pytest.fixture
def mock_paper():
    return Paper(
        id="2301.12345",
        title="Test Paper",
        link="https://arxiv.org/abs/2301.12345",
        pdf="https://arxiv.org/pdf/2301.12345.pdf",
        summary="Test summary",
        authors=["Author One", "Author Two"],
        updated="2023-01-15",
        categories=["cs.AI", "cs.LG"],
    )


@pytest.fixture
def mock_cache_payload():
    return {
        "content": "Abstract\n\nThis is a test paper.\n\n1 Introduction\n\nContent here.",
        "content_hash": "abc123",
        "content_length": 60,
        "sections": [
            {
                "number": 1,
                "title": "Abstract",
                "start_offset": 0,
                "end_offset": 2,
                "snippet": "Abstract\n\nThis is a test paper.",
            },
            {
                "number": 2,
                "title": "1 Introduction",
                "start_offset": 4,
                "end_offset": 6,
                "snippet": "1 Introduction\n\nContent here.",
            },
        ],
        "toc_flat": ["Abstract", "1 Introduction"],
        "format": "plain",
    }


@pytest.mark.asyncio
async def test_get_digest_details_with_cached_content(mock_paper, mock_cache_payload):
    from types import SimpleNamespace
    feed_entry = SimpleNamespace(
        id="http://arxiv.org/abs/2301.12345v1",
        title=mock_paper.title,
        link=mock_paper.link,
        summary=mock_paper.summary,
        authors=[SimpleNamespace(name=n) for n in mock_paper.authors],
        links=[SimpleNamespace(type="application/pdf", href=mock_paper.pdf)],
        tags=[SimpleNamespace(term=t) for t in mock_paper.categories],
        updated=mock_paper.updated,
    )
    feed = SimpleNamespace(entries=[feed_entry])

    with (
        patch("feedparser.parse", return_value=feed),
        patch("src.api.deps.get_index_holder", return_value=None),
        patch("src.api.routers.digest.get_cached", return_value=mock_cache_payload),
        patch("src.api.routers.digest.mcp_download_paper") as mock_download,
        patch("src.api.routers.digest.mcp_read_paper") as mock_read,
    ):
        result = await get_digest_details("2301.12345")
        
        assert result.paper_id == "2301.12345"
        assert result.sections == mock_cache_payload["sections"]
        assert result.toc_flat == mock_cache_payload["toc_flat"]
        assert result.content_length == 60
        assert result.content_hash == "abc123"
        assert result.has_full_text is True
        
        mock_download.assert_not_called()
        mock_read.assert_not_called()


@pytest.mark.asyncio
async def test_get_digest_details_without_cache(mock_paper, mock_cache_payload):
    from types import SimpleNamespace
    feed_entry = SimpleNamespace(
        id="http://arxiv.org/abs/2301.12345v1",
        title=mock_paper.title,
        link=mock_paper.link,
        summary=mock_paper.summary,
        authors=[SimpleNamespace(name=n) for n in mock_paper.authors],
        links=[SimpleNamespace(type="application/pdf", href=mock_paper.pdf)],
        tags=[SimpleNamespace(term=t) for t in mock_paper.categories],
        updated=mock_paper.updated,
    )
    feed = SimpleNamespace(entries=[feed_entry])

    with (
        patch("feedparser.parse", return_value=feed),
        patch("src.api.deps.get_index_holder", return_value=None),
        patch("src.api.routers.digest.get_cached", return_value=None),
        patch("src.api.routers.digest.mcp_download_paper", return_value=True) as mock_download,
        patch("src.api.routers.digest.mcp_read_paper", return_value=mock_cache_payload["content"]) as mock_read,
        patch("src.api.routers.digest.set_cached") as mock_set_cache,
        patch("src.api.routers.digest.build_sections", return_value={"sections": mock_cache_payload["sections"], "toc_flat": mock_cache_payload["toc_flat"]}),
        patch("src.api.routers.digest.compute_hash", return_value="abc123"),
    ):
        result = await get_digest_details("2301.12345")
        
        assert result.has_full_text is True
        assert result.sections is not None
        assert result.content_length == len(mock_cache_payload["content"])
        
        mock_download.assert_called_once_with("2301.12345")
        mock_read.assert_called_once_with("2301.12345", fmt="plain")
        mock_set_cache.assert_called_once()


@pytest.mark.asyncio
async def test_get_digest_details_mcp_failure(mock_paper):
    from types import SimpleNamespace
    feed_entry = SimpleNamespace(
        id="http://arxiv.org/abs/2301.12345v1",
        title=mock_paper.title,
        link=mock_paper.link,
        summary=mock_paper.summary,
        authors=[SimpleNamespace(name=n) for n in mock_paper.authors],
        links=[SimpleNamespace(type="application/pdf", href=mock_paper.pdf)],
        tags=[SimpleNamespace(term=t) for t in mock_paper.categories],
        updated=mock_paper.updated,
    )
    feed = SimpleNamespace(entries=[feed_entry])

    with (
        patch("feedparser.parse", return_value=feed),
        patch("src.api.deps.get_index_holder", return_value=None),
        patch("src.api.routers.digest.get_cached", return_value=None),
        patch("src.api.routers.digest.mcp_download_paper", return_value=False),
    ):
        result = await get_digest_details("2301.12345")
        
        assert result.has_full_text is False
        assert result.sections is None
        assert result.content_length is None
