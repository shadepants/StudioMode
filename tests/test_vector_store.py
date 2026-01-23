"""
Unit Tests for VectorStore Service
===================================
Tests the LanceDB-backed memory storage system.
"""

import pytest
import tempfile
import os
import shutil
import time


class TestVectorStore:
    """Test suite for VectorStore class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a temporary database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_lancedb")
        
        # Import here to allow patching config
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".core")))
        
        # Patch config values before import
        from unittest.mock import patch
        with patch.dict('os.environ', {
            'EMBEDDING_MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2'
        }):
            from services.vector_store import VectorStore
            self.store = VectorStore(self.db_path)
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_semantic_memory(self):
        """Test adding semantic (non-episodic) memory."""
        entry_id = self.store.add(
            text="Python is a programming language",
            type="semantic",
            metadata={"source": "test"}
        )
        
        assert entry_id is not None
        assert len(entry_id) == 36  # UUID format
    
    def test_add_episodic_memory_with_chaining(self):
        """Test episodic memory creates chain via prev_id."""
        id1 = self.store.add("First event", "episodic")
        id2 = self.store.add("Second event", "episodic")
        
        assert id1 != id2
        assert self.store.last_episodic_id == id2
    
    def test_buffer_flush(self):
        """Test buffer flushes when reaching BUFFER_SIZE."""
        # Add entries up to buffer size
        from config import BUFFER_SIZE
        
        for i in range(BUFFER_SIZE):
            self.store.add(f"Event {i}", "episodic")
        
        # Buffer should be empty after flush
        assert len(self.store.buffer) == 0
    
    def test_search_returns_results(self):
        """Test semantic search returns relevant results."""
        self.store.add("Machine learning is a subset of AI", "semantic")
        self.store.add("Python is great for data science", "semantic")
        self.store.add("The weather is nice today", "semantic")
        
        results = self.store.search("artificial intelligence", limit=2)
        
        assert len(results) <= 2
        # First result should be about ML/AI
        if results:
            assert "machine" in results[0]["text"].lower() or "ai" in results[0]["text"].lower()
    
    def test_search_with_filter(self):
        """Test search respects type filter."""
        self.store.add("Semantic content", "semantic")
        self.store.add("Episodic content", "episodic")
        self.store.flush()
        
        results = self.store.search("content", limit=5, filter_type="semantic")
        
        for r in results:
            assert r["type"] == "semantic"
    
    def test_get_feed_returns_recent(self):
        """Test feed returns recent episodic entries."""
        for i in range(5):
            self.store.add(f"Event {i}", "episodic")
        self.store.flush()
        
        feed = self.store.get_feed(limit=3)
        
        assert len(feed) <= 3
        # Should be newest first
        if len(feed) >= 2:
            assert feed[0]["timestamp"] >= feed[1]["timestamp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
