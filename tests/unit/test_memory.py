"""
Unit tests for memory components.

Tests embedder, FAISS backend, ChromaDB backend, and VectorMemory.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.memory import BGEEmbedder, FAISSBackend, ChromaDBBackend, VectorMemory, VectorBackendType
from src.core.exceptions import VectorMemoryError, EmbeddingError


class TestBGEEmbedder:
    """Test BGE embedder"""
    
    @pytest.fixture
    def mock_embedder(self):
        """Mock embedder for testing without actual model"""
        with patch('src.memory.embedder.OPENVINO_AVAILABLE', True):
            with patch('src.memory.embedder.OVModelForFeatureExtraction'):
                with patch('src.memory.embedder.AutoTokenizer'):
                    embedder = Mock(spec=BGEEmbedder)
                    embedder.dimension = 768
                    embedder.embed = Mock(return_value=np.random.rand(2, 768))
                    embedder.embed_single = Mock(return_value=np.random.rand(768))
                    embedder.similarity = Mock(return_value=0.85)
                    return embedder
    
    def test_embed_dimension(self, mock_embedder):
        """Test embedding dimension"""
        result = mock_embedder.embed(["test"])
        assert result.shape[1] == 768
    
    def test_embed_batch(self, mock_embedder):
        """Test batch embedding"""
        texts = ["text1", "text2"]
        result = mock_embedder.embed(texts)
        assert result.shape == (2, 768)
    
    def test_similarity(self, mock_embedder):
        """Test similarity calculation"""
        sim = mock_embedder.similarity("text1", "text2")
        assert 0 <= sim <= 1


class TestFAISSBackend:
    """Test FAISS backend"""
    
    @pytest.fixture
    def faiss_backend(self):
        """Create FAISS backend for testing"""
        try:
            return FAISSBackend(dimension=768)
        except:
            pytest.skip("FAISS not available")
    
    def test_initialization(self, faiss_backend):
        """Test backend initialization"""
        assert faiss_backend.dimension == 768
        assert faiss_backend.index.ntotal == 0
    
    def test_add_vectors(self, faiss_backend):
        """Test adding vectors"""
        embeddings = np.random.rand(10, 768).astype('float32')
        ids = faiss_backend.add(embeddings)
        
        assert len(ids) == 10
        assert faiss_backend.index.ntotal == 10
    
    def test_search(self, faiss_backend):
        """Test similarity search"""
        # Add vectors
        embeddings = np.random.rand(100, 768).astype('float32')
        faiss_backend.add(embeddings)
        
        # Search
        query = np.random.rand(768).astype('float32')
        results = faiss_backend.search(query, k=5)
        
        assert len(results) == 5
        assert all('distance' in r for r in results)
        assert all('score' in r for r in results)
    
    def test_search_batch(self, faiss_backend):
        """Test batch search"""
        embeddings = np.random.rand(100, 768).astype('float32')
        faiss_backend.add(embeddings)
        
        queries = np.random.rand(3, 768).astype('float32')
        results = faiss_backend.search_batch(queries, k=5)
        
        assert len(results) == 3
        assert all(len(r) == 5 for r in results)
    
    def test_metadata(self, faiss_backend):
        """Test metadata storage"""
        embeddings = np.random.rand(5, 768).astype('float32')
        metadata = [{"text": f"doc{i}"} for i in range(5)]
        
        ids = faiss_backend.add(embeddings, metadata=metadata)
        
        query = embeddings[0]
        results = faiss_backend.search(query, k=1)
        
        assert results[0]['metadata']['text'] == 'doc0'
    
    def test_stats(self, faiss_backend):
        """Test statistics"""
        embeddings = np.random.rand(10, 768).astype('float32')
        faiss_backend.add(embeddings)
        
        stats = faiss_backend.get_stats()
        assert stats['total_vectors'] == 10
        assert stats['dimension'] == 768


class TestChromaDBBackend:
    """Test ChromaDB backend"""
    
    @pytest.fixture
    def chromadb_backend(self, tmp_path):
        """Create ChromaDB backend for testing"""
        try:
            return ChromaDBBackend(
                collection_name="test_collection",
                persist_directory=str(tmp_path / "chroma"),
                dimension=768
            )
        except:
            pytest.skip("ChromaDB not available")
    
    def test_initialization(self, chromadb_backend):
        """Test backend initialization"""
        assert chromadb_backend.dimension == 768
        assert chromadb_backend.collection.count() == 0
    
    def test_add_vectors(self, chromadb_backend):
        """Test adding vectors"""
        embeddings = np.random.rand(10, 768).astype('float32')
        ids = chromadb_backend.add(embeddings)
        
        assert len(ids) == 10
        assert chromadb_backend.collection.count() == 10
    
    def test_search(self, chromadb_backend):
        """Test similarity search"""
        embeddings = np.random.rand(50, 768).astype('float32')
        chromadb_backend.add(embeddings)
        
        query = np.random.rand(768).astype('float32')
        results = chromadb_backend.search(query, k=5)
        
        assert len(results) <= 5
        assert all('distance' in r for r in results)
    
    def test_metadata_filtering(self, chromadb_backend):
        """Test metadata filtering"""
        embeddings = np.random.rand(10, 768).astype('float32')
        metadata = [{"category": "A" if i % 2 == 0 else "B"} for i in range(10)]
        
        chromadb_backend.add(embeddings, metadata=metadata)
        
        query = np.random.rand(768).astype('float32')
        results = chromadb_backend.search(query, k=10, where={"category": "A"})
        
        assert all(r['metadata']['category'] == 'A' for r in results)
    
    def test_update(self, chromadb_backend):
        """Test updating vectors"""
        embeddings = np.random.rand(5, 768).astype('float32')
        ids = chromadb_backend.add(embeddings)
        
        new_metadata = [{"updated": True} for _ in range(5)]
        chromadb_backend.update(ids, metadata=new_metadata)
        
        # Verify update
        results = chromadb_backend.peek(limit=5)
        assert all(m.get('updated') for m in results['metadatas'])
    
    def test_delete(self, chromadb_backend):
        """Test deleting vectors"""
        embeddings = np.random.rand(10, 768).astype('float32')
        ids = chromadb_backend.add(embeddings)
        
        chromadb_backend.delete(ids[:5])
        
        assert chromadb_backend.collection.count() == 5


class TestVectorMemory:
    """Test unified VectorMemory interface"""
    
    @pytest.fixture(params=["faiss", "chromadb"])
    def vector_memory(self, request, tmp_path):
        """Create VectorMemory with different backends"""
        try:
            if request.param == "chromadb":
                from src.memory.embedder import get_embedder
                with patch.object(get_embedder(), 'embed', return_value=np.random.rand(1, 768)):
                    return VectorMemory(
                        backend=request.param,
                        persist_directory=str(tmp_path / "test_memory")
                    )
            else:
                from src.memory.embedder import get_embedder
                with patch.object(get_embedder(), 'embed', return_value=np.random.rand(1, 768)):
                    return VectorMemory(backend=request.param)
        except:
            pytest.skip(f"{request.param} not available")
    
    def test_add_texts(self, vector_memory):
        """Test adding texts"""
        with patch.object(vector_memory.embedder, 'embed', return_value=np.random.rand(3, 768)):
            texts = ["doc1", "doc2", "doc3"]
            ids = vector_memory.add_texts(texts)
            
            assert len(ids) == 3
    
    def test_search(self, vector_memory):
        """Test search with text"""
        # Add documents
        with patch.object(vector_memory.embedder, 'embed', return_value=np.random.rand(10, 768)):
            texts = [f"document {i}" for i in range(10)]
            vector_memory.add_texts(texts)
        
        # Search
        with patch.object(vector_memory.embedder, 'embed_single', return_value=np.random.rand(768)):
            results = vector_memory.search("query", k=3)
            
            assert len(results) <= 3
    
    def test_stats(self, vector_memory):
        """Test getting stats"""
        stats = vector_memory.get_stats()
        assert 'total_vectors' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
