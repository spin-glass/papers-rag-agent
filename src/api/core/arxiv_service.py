"""ArXiv service for searching papers."""

from typing import List, Dict, Any
from retrieval.arxiv_searcher import run_arxiv_search


async def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search ArXiv for papers.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of paper dictionaries
    """
    try:
        # Use existing ArXiv searcher
        results = run_arxiv_search(query, max_results=max_results)

        # Convert to expected format
        formatted_results = []
        for paper in results:
            formatted_results.append({
                "id": paper.get("id", ""),
                "title": paper.get("title", ""),
                "url": paper.get("link", ""),
                "summary": paper.get("summary", ""),
                "authors": paper.get("authors", []),
                "pdf": paper.get("pdf", ""),
                "categories": paper.get("categories", []),
                "updated": paper.get("updated", "")
            })

        return formatted_results

    except Exception as e:
        # Return empty results on error
        return []
