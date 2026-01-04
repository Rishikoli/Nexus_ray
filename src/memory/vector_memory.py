"""
Vector memory system for semantic search and retrieval.

Provides unified interface for vector storage with multiple backends.
"""

from typing import List, Dict, Any, Optional, Union
import numpy as np
from enum import Enum
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import VectorMemoryError
from src.memory.embedder import BGEEmbedder, get_embedder
from src.memory.reranker import get_reranker

# ... (inside search method)


from src.memory.faiss_backend import FAISSBackend
from src.memory.chromadb_backend import ChromaDBBackend


class VectorBackendType(str, Enum):
    """Supported vector store backends"""
    FAISS = "faiss"
    CHROMADB = "chromadb"


class VectorMemory:
    """
    Unified vector memory interface.
    
    Features:
    - Automatic embedding generation
    - Multiple backend support (FAISS, ChromaDB)
    - Semantic search
    - Context-aware retrieval
    
    Usage:
        memory = VectorMemory(backend="faiss")
        memory.add_texts(["document 1", "document 2"])
        results = memory.search("query text", k=5)
    """
    
    def __init__(
        self,
        backend: Union[str, VectorBackendType] = VectorBackendType.FAISS,
        embedder: Optional[BGEEmbedder] = None,
        **backend_kwargs
    ):
        """
        Initialize vector memory.
        
        Args:
            backend: Backend type (faiss or chromadb)
            embedder: Custom embedder (uses default if None)
            **backend_kwargs: Additional backend-specific arguments
        """
        self.settings = get_settings()
        
        # Initialize embedder
        self.embedder = embedder or get_embedder()
        self.dimension = self.embedder.get_dimension()
        
        # Initialize backend
        backend_type = VectorBackendType(backend) if isinstance(backend, str) else backend
        self.backend = self._create_backend(backend_type, **backend_kwargs)
        
        logger.info(f"✅ VectorMemory initialized (backend={backend_type.value}, dim={self.dimension})")
    
    def _create_backend(self, backend_type: VectorBackendType, **kwargs):
        """Create backend instance"""
        kwargs.setdefault('dimension', self.dimension)
        
        if backend_type == VectorBackendType.FAISS:
            return FAISSBackend(
                index_type=self.settings.memory.index_type,
                **kwargs
            )
        
        elif backend_type == VectorBackendType.CHROMADB:
            return ChromaDBBackend(
                collection_name=self.settings.memory.collection_name,
                persist_directory=self.settings.memory.persist_directory,
                **kwargs
            )
        
        else:
            raise VectorMemoryError(f"Unsupported backend: {backend_type}")
    
    def add_texts(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[Union[int, str]]:
        """
        Add texts to memory (auto-generates embeddings).
        
        Args:
            texts: List of text documents
            metadata: Optional metadata for each text
            ids: Optional custom IDs
            
        Returns:
            List of assigned IDs
        """
        if not texts:
            raise VectorMemoryError("No texts provided")
        
        # Generate embeddings
        logger.debug(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.embedder.embed(texts, normalize=True)
        
        # Add to backend
        return self.backend.add(embeddings, metadata=metadata, ids=ids)
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[Union[int, str]]:
        """
        Add pre-computed embeddings to memory.
        
        Args:
            embeddings: Numpy array of embeddings
            metadata: Optional metadata
            ids: Optional custom IDs
            
        Returns:
            List of assigned IDs
        """
        return self.backend.add(embeddings, metadata=metadata, ids=ids)
    
    def search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using text query.
        
        Args:
            query: Text query
            k: Number of results
            where: Metadata filter (ChromaDB only)
            return_metadata: Whether to include metadata
            
        Returns:
            List of results with scores and metadata
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_single(query, normalize=True)
        
        # 1. Retrieve Candidates (Fetch 3x k to give re-ranker enough candidates)
        initial_k = k * 3
        
        # Search backend
        if isinstance(self.backend, ChromaDBBackend) and where:
            results = self.backend.search(query_embedding, k=initial_k, where=where, return_metadata=return_metadata)
        else:
            results = self.backend.search(query_embedding, k=initial_k, return_metadata=return_metadata)
            
        # 2. Re-rank if reranker is available
        reranker = get_reranker()
        if reranker:
            # Extract texts
            docs = [r['text'] for r in results if 'text' in r]
            if docs:
                # Top k reranking
                reranked = reranker.rerank(query, docs)
                
                # Re-order results based on reranker scores
                new_results = []
                for item in reranked:
                    original_idx = item['index']
                    if original_idx < len(results):
                        original_res = results[original_idx]
                        original_res['score'] = item['score']  # Update score
                        new_results.append(original_res)
                
                results = new_results
        
        # Return top k
        return results[:k]
    
    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search using pre-computed embedding.
        
        Args:
            query_embedding: Query vector
            k: Number of results
            return_metadata: Whether to include metadata
            
        Returns:
            List of results
        """
        return self.backend.search(query_embedding, k=k, return_metadata=return_metadata)
    
    def delete(self, ids: List[Union[int, str]]) -> int:
        """Delete documents by IDs"""
        return self.backend.delete(ids)
    
    def clear(self):
        """Clear all documents from memory"""
        self.backend.clear()
    
    def save(self, path: Optional[str] = None):
        """Save memory to disk (FAISS only)"""
        if hasattr(self.backend, 'save'):
            self.backend.save(path)
        else:
            logger.warning(f"Backend {type(self.backend).__name__} doesn't support save")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return self.backend.get_stats()
    
    def __repr__(self) -> str:
        return f"VectorMemory(backend={type(self.backend).__name__}, {self.backend.get_stats()['total_vectors']} vectors)"


# Singleton instances for different use cases
_vector_memories: Dict[str, VectorMemory] = {}


def get_vector_memory(
    name: str = "default",
    backend: Optional[str] = None,
    **kwargs
) -> VectorMemory:
    """
    Get or create named vector memory instance.
    
    Args:
        name: Memory name (for multiple isolated memories)
        backend: Backend type (uses config default if None)
        **kwargs: Additional backend arguments
        
    Returns:
        VectorMemory instance
    """
    if name not in _vector_memories:
        settings = get_settings()
        backend = backend or settings.memory.backend
        _vector_memories[name] = VectorMemory(backend=backend, **kwargs)
    
    return _vector_memories[name]
