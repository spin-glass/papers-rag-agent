"""
Cache loading utilities for precomputed RAG data.
"""

import json
import pickle
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from models import Paper
from retrieval.inmemory import InMemoryIndex


def load_precomputed_cache() -> Optional[InMemoryIndex]:
    """
    Load precomputed papers and embeddings cache.
    
    Returns:
        InMemoryIndex with precomputed data, or None if loading fails
    """
    try:
        data_dir = Path(__file__).parent
        papers_file = data_dir / "precomputed_papers.json"
        embeddings_file = data_dir / "precomputed_embeddings.pkl"
        
        # Check if cache files exist
        if not papers_file.exists():
            print(f"⚠️  Papers cache not found: {papers_file}")
            return None
            
        if not embeddings_file.exists():
            print(f"⚠️  Embeddings cache not found: {embeddings_file}")
            return None
        
        print("📖 Loading precomputed cache...")
        
        # Load papers
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        papers = [Paper(**data) for data in papers_data]
        print(f"  ✅ Loaded {len(papers)} papers")
        
        # Load embeddings
        with open(embeddings_file, 'rb') as f:
            papers_with_embeddings = pickle.load(f)
        
        print(f"  ✅ Loaded {len(papers_with_embeddings)} embeddings")
        
        # Create index and populate with precomputed data
        index = InMemoryIndex()
        index.papers_with_embeddings = papers_with_embeddings
        
        print("✅ Precomputed cache loaded successfully!")
        return index
        
    except Exception as e:
        print(f"❌ Error loading precomputed cache: {e}")
        import traceback
        traceback.print_exc()
        return None


def cache_exists() -> bool:
    """
    Check if precomputed cache files exist.
    
    Returns:
        True if both cache files exist, False otherwise
    """
    data_dir = Path(__file__).parent
    papers_file = data_dir / "precomputed_papers.json"
    embeddings_file = data_dir / "precomputed_embeddings.pkl"
    
    return papers_file.exists() and embeddings_file.exists()


def get_cache_info() -> dict:
    """
    Get information about the cache files.
    
    Returns:
        Dictionary with cache file information
    """
    data_dir = Path(__file__).parent
    papers_file = data_dir / "precomputed_papers.json"
    embeddings_file = data_dir / "precomputed_embeddings.pkl"
    
    info = {
        "papers_file": str(papers_file),
        "embeddings_file": str(embeddings_file),
        "papers_exists": papers_file.exists(),
        "embeddings_exists": embeddings_file.exists(),
    }
    
    if papers_file.exists():
        info["papers_size"] = papers_file.stat().st_size
        info["papers_modified"] = papers_file.stat().st_mtime
    
    if embeddings_file.exists():
        info["embeddings_size"] = embeddings_file.stat().st_size
        info["embeddings_modified"] = embeddings_file.stat().st_mtime
    
    return info
