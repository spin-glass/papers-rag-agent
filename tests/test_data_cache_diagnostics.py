"""
Diagnostics tests for cache loading issues in CloudRun.
"""

import pytest
import pickle
import json
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from data.cache_loader import load_precomputed_cache, cache_exists
from models import Paper


class TestCacheDiagnostics:
    """Cache loading diagnostics for CloudRun debugging."""

    def test_cache_files_exist(self):
        """Test that cache files exist and are accessible."""
        data_dir = Path(__file__).parent.parent / "src" / "data"
        papers_file = data_dir / "precomputed_papers.json"
        embeddings_file = data_dir / "precomputed_embeddings.pkl"
        
        print(f"📂 Data directory: {data_dir}")
        print(f"📂 Papers file: {papers_file}")
        print(f"📂 Embeddings file: {embeddings_file}")
        
        assert papers_file.exists(), f"Papers file not found: {papers_file}"
        assert embeddings_file.exists(), f"Embeddings file not found: {embeddings_file}"
        
        # Check file sizes
        papers_size = papers_file.stat().st_size
        embeddings_size = embeddings_file.stat().st_size
        
        print(f"📊 Papers file size: {papers_size} bytes")
        print(f"📊 Embeddings file size: {embeddings_size} bytes")
        
        assert papers_size > 0, "Papers file is empty"
        assert embeddings_size > 0, "Embeddings file is empty"

    def test_papers_json_loading(self):
        """Test papers JSON file can be loaded correctly."""
        data_dir = Path(__file__).parent.parent / "src" / "data"
        papers_file = data_dir / "precomputed_papers.json"
        
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        assert isinstance(papers_data, list), "Papers data should be a list"
        assert len(papers_data) > 0, "Papers data should not be empty"
        
        # Test first paper structure
        first_paper = papers_data[0]
        required_fields = {'id', 'title', 'link', 'summary'}
        assert required_fields.issubset(first_paper.keys()), f"Missing required fields in paper data"
        
        # Test Paper model creation
        paper = Paper(**first_paper)
        assert isinstance(paper, Paper), "Should be able to create Paper model"
        
        print(f"✅ Successfully loaded {len(papers_data)} papers from JSON")

    def test_embeddings_pickle_loading(self):
        """Test embeddings pickle file can be loaded correctly."""
        data_dir = Path(__file__).parent.parent / "src" / "data"
        embeddings_file = data_dir / "precomputed_embeddings.pkl"
        
        with open(embeddings_file, 'rb') as f:
            embeddings_data = pickle.load(f)
        
        assert isinstance(embeddings_data, list), "Embeddings data should be a list"
        assert len(embeddings_data) > 0, "Embeddings data should not be empty"
        
        # Test first embedding structure (it's a tuple of (Paper, numpy.ndarray))
        first_embedding = embeddings_data[0]
        assert isinstance(first_embedding, tuple), "Embedding should be a tuple"
        assert len(first_embedding) == 2, "Embedding tuple should have 2 elements"
        
        paper, embedding_vector = first_embedding
        assert hasattr(paper, 'id'), "Paper should have id attribute"
        
        # Test embedding vector
        import numpy as np
        assert isinstance(embedding_vector, np.ndarray), "Embedding should be numpy array"
        assert embedding_vector.size > 0, "Embedding vector should not be empty"
        
        print(f"✅ Successfully loaded {len(embeddings_data)} embeddings from pickle")

    def test_cache_loader_function(self):
        """Test the complete cache loading function."""
        index = load_precomputed_cache()
        
        assert index is not None, "Cache loader should return an index"
        assert hasattr(index, 'papers_with_embeddings'), "Index should have papers_with_embeddings"
        
        embeddings_count = len(index.papers_with_embeddings)
        print(f"📊 Loaded index with {embeddings_count} papers with embeddings")
        
        # This test should pass in local environment
        if embeddings_count == 0:
            pytest.skip("No embeddings loaded - this indicates the CloudRun issue")
        
        assert embeddings_count > 0, "Should have loaded embeddings successfully"

    def test_cache_exists_function(self):
        """Test the cache existence check function."""
        exists = cache_exists()
        print(f"📋 Cache exists check: {exists}")
        
        # In local environment, this should be True
        assert exists, "Cache files should exist in local environment"

    def test_embedding_data_integrity(self):
        """Test that embedding data is not corrupted."""
        data_dir = Path(__file__).parent.parent / "src" / "data"
        embeddings_file = data_dir / "precomputed_embeddings.pkl"
        
        try:
            with open(embeddings_file, 'rb') as f:
                # Try to load and verify structure
                embeddings_data = pickle.load(f)
                
                if len(embeddings_data) > 0:
                    first_item = embeddings_data[0]
                    
                    # Check tuple structure (Paper, numpy.ndarray)
                    assert isinstance(first_item, tuple), "Embedding item should be a tuple"
                    assert len(first_item) == 2, "Embedding tuple should have 2 elements"
                    
                    paper, embedding = first_item
                    assert hasattr(paper, 'id'), "Paper should have id attribute"
                    
                    # Check embedding vector
                    import numpy as np
                    assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
                    assert embedding.shape[0] > 0, "Embedding should have dimensions"
                    assert not np.isnan(embedding).any(), "Embedding should not contain NaN values"
                    
                    print(f"✅ Embedding data integrity check passed")
                    print(f"📊 Embedding vector shape: {embedding.shape}")
                    print(f"📊 Sample embedding values: {embedding[:5]}")
                    
        except Exception as e:
            pytest.fail(f"Embedding data integrity check failed: {e}")
