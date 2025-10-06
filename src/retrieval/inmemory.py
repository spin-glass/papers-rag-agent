"""In-memory vector index for RAG retrieval."""

import numpy as np
from typing import List, Tuple
from models import Paper, RetrievedContext
from llm.embeddings import get_embed


class InMemoryIndex:
    """Simple in-memory vector index using cosine similarity."""

    def __init__(self):
        """Initialize empty index."""
        self.papers_with_embeddings: List[Tuple[Paper, np.ndarray]] = []

    def build(self, papers: List[Paper]) -> None:
        """
        Build index from list of papers.

        Args:
            papers: List of Paper objects with title and summary
        """
        self.papers_with_embeddings = []

        for paper in papers:
            # Combine title and summary for embedding
            text = f"{paper.title}\n\n{paper.summary}"

            try:
                # Get embedding for the combined text
                embedding = get_embed(text)
                self.papers_with_embeddings.append((paper, embedding))

            except Exception as e:
                print(f"Warning: Failed to embed paper {paper.id}: {e}")
                continue

        print(f"Built index with {len(self.papers_with_embeddings)} papers")

    def search(self, query: str, k: int) -> List[RetrievedContext]:
        """
        Search for top-k most similar papers.

        Args:
            query: Search query text
            k: Number of top results to return

        Returns:
            List of RetrievedContext objects ordered by similarity
        """
        if not self.papers_with_embeddings:
            return []

        try:
            # Get query embedding
            query_embedding = get_embed(query)

        except Exception as e:
            print(f"Error: Failed to embed query: {e}")
            return []

        # Calculate cosine similarities
        similarities = []
        for paper, paper_embedding in self.papers_with_embeddings:
            # Cosine similarity = dot product of normalized vectors
            similarity = self._cosine_similarity(query_embedding, paper_embedding)
            similarities.append((similarity, paper, paper_embedding))

        # Sort by similarity (descending) and take top-k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_results = similarities[:k]

        # Convert to RetrievedContext objects
        contexts = []
        for similarity, paper, embedding in top_results:
            context = RetrievedContext(
                paper_id=paper.id,
                title=paper.title,
                link=paper.link,
                summary=paper.summary,
                embedding=embedding,
            )
            contexts.append(context)

        return contexts

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            a, b: Input vectors

        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        a_norm = a / (np.linalg.norm(a) + 1e-8)
        b_norm = b / (np.linalg.norm(b) + 1e-8)

        # Dot product of normalized vectors
        similarity = np.dot(a_norm, b_norm)

        # Clamp to [0, 1] range
        return max(0.0, float(similarity))
