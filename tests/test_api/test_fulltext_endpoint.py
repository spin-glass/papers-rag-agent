import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.api.routers.digest import get_fulltext


@pytest.fixture
def mock_content():
    return "Abstract\n\nThis is test content.\n\n1 Introduction\n\nMore content here."


@pytest.mark.asyncio
async def test_get_fulltext_from_cache(mock_content):
    cache_payload = {
        "content": mock_content,
        "format": "plain",
        "content_hash": "abc123",
    }
    
    with (
        patch("src.api.routers.digest.get_cached", return_value=cache_payload),
        patch("src.api.routers.digest.mcp_download_paper") as mock_download,
        patch("src.api.routers.digest.mcp_read_paper") as mock_read,
    ):
        result = await get_fulltext("2301.12345", format="plain", max_bytes=200000)
        
        assert result.body.decode() == mock_content
        mock_download.assert_not_called()
        mock_read.assert_not_called()


@pytest.mark.asyncio
async def test_get_fulltext_on_demand(mock_content):
    with (
        patch("src.api.routers.digest.get_cached", return_value=None),
        patch("src.api.routers.digest.mcp_download_paper", return_value=True) as mock_download,
        patch("src.api.routers.digest.mcp_read_paper", return_value=mock_content) as mock_read,
        patch("src.api.routers.digest.set_cached") as mock_set_cache,
        patch("src.api.routers.digest.build_sections", return_value={"sections": [], "toc_flat": []}),
        patch("src.api.routers.digest.compute_hash", return_value="abc123"),
    ):
        result = await get_fulltext("2301.12345", format="plain", max_bytes=200000)
        
        assert result.body.decode() == mock_content
        mock_download.assert_called_once_with("2301.12345")
        mock_read.assert_called_once_with("2301.12345", fmt="plain")
        mock_set_cache.assert_called_once()


@pytest.mark.asyncio
async def test_get_fulltext_truncation(mock_content):
    cache_payload = {
        "content": mock_content,
        "format": "plain",
    }
    
    with patch("src.api.routers.digest.get_cached", return_value=cache_payload):
        result = await get_fulltext("2301.12345", format="plain", max_bytes=20)
        
        assert len(result.body.decode()) == 20
        assert result.body.decode() == mock_content[:20]


@pytest.mark.asyncio
async def test_get_fulltext_download_failure():
    with (
        patch("src.api.routers.digest.get_cached", return_value=None),
        patch("src.api.routers.digest.mcp_download_paper", return_value=False),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_fulltext("2301.12345", format="plain", max_bytes=200000)
        
        assert exc_info.value.status_code == 404
        assert "Could not download" in exc_info.value.detail
