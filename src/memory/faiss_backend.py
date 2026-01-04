"""
FAISS backend for fast vector similarity search.

Provides high-performance in-memory vector search using Facebook's FAISS library.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
from loguru import logger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. Install with: pip install faiss-cpu")

from src.core.config import get_settings
from src.core.exceptions import VectorMemoryError


class FAISSBackend:
    """
    FAISS-based vector store for fast similarity search.
    
    Features:
    - Ultra-fast similarity search (microseconds)
    - Multiple index types (Flat, IVF, HNSW)
    - In-memory operation
    - Optional persistence to disk
    
    Performance:
    - Flat: Exact search, ~1M vectors/sec
    - IVF: Approximate search, ~10M+ vectors/sec
    """
    
    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "IndexFlatL2",
        persist_path: Optional[str] = None
    ):
        """
        Initialize FAISS backend.
        
        Args:
            dimension: Embedding dimension
            index_type: FAISS index type (IndexFlatL2, IndexIVFFlat, etc.)
            persist_path: Path to save/load index
        """
        if not FAISS_AVAILABLE:
            raise VectorMemoryError("FAISS not available - install faiss-cpu")
        
        self.dimension = dimension
        self.index_type = index_type
        self.persist_path = persist_path
        
        # Initialize index
        self.index = self._create_index()
        
        # Metadata storage (id -> metadata mapping)
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.id_counter = 0
        
        # Load existing index if available
        if self.persist_path and Path(self.persist_path).exists():
            self.load()
        
        logger.info(f"✅ FAISS backend initialized ({index_type}, dim={dimension})")
    
    def _create_index(self):
        """Create FAISS index based on type"""
        if self.index_type == "IndexFlatL2":
            # Exact L2 distance search
            return faiss.IndexFlatL2(self.dimension)
        
        elif self.index_type == "IndexFlatIP":
            # Exact inner product (cosine similarity with normalized vectors)
            return faiss.IndexFlatIP(self.dimension)
        
        elif self.index_type == "IndexIVFFlat":
            # Approximate search with inverted file index
            quantizer = faiss.IndexFlatL2(self.dimension)
            n_lists = 100  # Number of clusters
            return faiss.IndexIVFFlat(quantizer, self.dimension, n_lists)
        
        else:
            raise VectorMemoryError(f"Unsupported index type: {self.index_type}")
    
    def add(
        self,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Add embeddings to index.
        
        Args:
            embeddings: Numpy array of shape (n, dimension)
            metadata: Optional list of metadata dicts
            
        Returns:
            List of assigned IDs
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        if embeddings.shape[1] != self.dimension:
            raise VectorMemoryError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}"
            )
        
        n_vectors = len(embeddings)
        
        # Train index if needed (for IVF indices)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            logger.info(f"Training FAISS index on {n_vectors} vectors...")
            self.index.train(embeddings.astype('float32'))
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Store metadata
        ids = []
        for i in range(n_vectors):
            vector_id = self.id_counter
            self.metadata[vector_id] = metadata[i] if metadata else {}
            ids.append(vector_id)
            self.id_counter += 1
        
        logger.debug(f"Added {n_vectors} vectors to FAISS index (total: {self.index.ntotal})")
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector (1D or 2D array)
            k: Number of results to return
            return_metadata: Whether to include metadata
            
        Returns:
            List of results with distances and metadata
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        if query_embedding.shape[1] != self.dimension:
            raise VectorMemoryError(
                f"Query dimension mismatch: expected {self.dimension}, got {query_embedding.shape[1]}"
            )
        
        # Search
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            min(k, self.index.ntotal)
        )
        
        # Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for not found
                continue
            
            result = {
                "id": int(idx),
                "distance": float(dist),
                "score": self._distance_to_score(float(dist))
            }
            
            if return_metadata and idx in self.metadata:
                result["metadata"] = self.metadata[idx]
            
            results.append(result)
        
        return results
    
    def search_batch(
        self,
        query_embeddings: np.ndarray,
        k: int = 5,
        return_metadata: bool = True
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch search for similar vectors.
        
        Args:
            query_embeddings: Query vectors (2D array)
            k: Number of results per query
            return_metadata: Whether to include metadata
            
        Returns:
            List of result lists
        """
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(
            query_embeddings.astype('float32'),
            min(k, self.index.ntotal)
        )
        
        # Format results for each query
        all_results = []
        for query_distances, query_indices in zip(distances, indices):
            results = []
            for dist, idx in zip(query_distances, query_indices):
                if idx == -1:
                    continue
                
                result = {
                    "id": int(idx),
                    "distance": float(dist),
                    "score": self._distance_to_score(float(dist))
                }
                
                if return_metadata and idx in self.metadata:
                    result["metadata"] = self.metadata[idx]
                
                results.append(result)
            
            all_results.append(results)
        
        return all_results
    
    def delete(self, ids: List[int]) -> int:
        """
        Delete vectors by IDs.
        
        Note: FAISS doesn't support efficient deletion. We only remove metadata.
        For true deletion, recreate the index without those vectors.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        deleted = 0
        for vector_id in ids:
            if vector_id in self.metadata:
                del self.metadata[vector_id]
                deleted += 1
        
        logger.warning(
            f"Deleted metadata for {deleted} vectors. "
            "Note: Vectors remain in FAISS index (rebuild index for true deletion)"
        )
        
        return deleted
    
    def save(self, path: Optional[str] = None):
        """
        Save index and metadata to disk.
        
        Args:
            path: Save path (uses persist_path if None)
        """
        save_path = path or self.persist_path
        if not save_path:
            raise VectorMemoryError("No save path specified")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save metadata
        metadata_path = save_path.with_suffix('.metadata.npy')
        np.save(metadata_path, self.metadata)
        
        logger.info(f"Saved FAISS index to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """
        Load index and metadata from disk.
        
        Args:
            path: Load path (uses persist_path if None)
        """
        load_path = path or self.persist_path
        if not load_path:
            raise VectorMemoryError("No load path specified")
        
        load_path = Path(load_path)
        if not load_path.exists():
            raise VectorMemoryError(f"Index file not found: {load_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load metadata
        metadata_path = load_path.with_suffix('.metadata.npy')
        if metadata_path.exists():
            self.metadata = np.load(metadata_path, allow_pickle=True).item()
            self.id_counter = max(self.metadata.keys()) + 1 if self.metadata else 0
        
        logger.info(f"Loaded FAISS index from {load_path} ({self.index.ntotal} vectors)")
    
    def clear(self):
        """Clear all vectors and metadata"""
        self.index = self._create_index()
        self.metadata = {}
        self.id_counter = 0
        logger.info("Cleared FAISS index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "is_trained": getattr(self.index, 'is_trained', True),
            "metadata_count": len(self.metadata)
        }
    
    @staticmethod
    def _distance_to_score(distance: float) -> float:
        """Convert L2 distance to similarity score in [0, 1]"""
        # Smaller distance = higher similarity
        return 1.0 / (1.0 + distance)
    
    def __repr__(self) -> str:
        return f"FAISSBackend(vectors={self.index.ntotal}, type={self.index_type}, dim={self.dimension})"
