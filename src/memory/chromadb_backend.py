"""
ChromaDB backend for persistent vector storage.

Provides persistent vector storage with built-in embeddings and metadata filtering.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not installed. Install with: pip install chromadb")

from src.core.config import get_settings
from src.core.exceptions import VectorMemoryError


class ChromaDBBackend:
    """
    ChromaDB-based vector store for persistent similarity search.
    
    Features:
    - Persistent storage (survives restarts)
    - Built-in metadata filtering
    - Automatic embedding generation (optional)
    - Multi-collection support
    
    Performance:
    - Slower than FAISS but persistent
    - Good for <1M vectors
    - Supports incremental updates
    """
    
    def __init__(
        self,
        collection_name: str = "nexus_ray_memory",
        persist_directory: Optional[str] = None,
        dimension: int = 768
    ):
        """
        Initialize ChromaDB backend.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistence
            dimension: Embedding dimension (for validation)
        """
        if not CHROMA_AVAILABLE:
            raise VectorMemoryError("ChromaDB not available - install chromadb")
        
        self.collection_name = collection_name
        self.dimension = dimension
        
        # Set up persist directory
        settings = get_settings()
        self.persist_directory = persist_directory or settings.memory.persist_directory
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"dimension": dimension}
        )
        
        logger.info(
            f"✅ ChromaDB backend initialized "
            f"(collection={collection_name}, persist={self.persist_directory})"
        )
    
    def add(
        self,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add embeddings to collection.
        
        Args:
            embeddings: Numpy array of shape (n, dimension)
            metadata: Optional list of metadata dicts
            ids: Optional list of IDs (generated if None)
            
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
        
        # Generate IDs if not provided
        if ids is None:
            current_count = self.collection.count()
            ids = [f"vec_{current_count + i}" for i in range(n_vectors)]
        
        # Prepare metadata (ChromaDB requires it)
        if metadata is None:
            metadata = [{} for _ in range(n_vectors)]
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings.tolist(),
            metadatas=metadata,
            ids=ids
        )
        
        logger.debug(f"Added {n_vectors} vectors to ChromaDB (total: {self.collection.count()})")
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector (1D or 2D array)
            k: Number of results to return
            where: Metadata filter (e.g., {"type": "document"})
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
        
        # Query collection
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k,
            where=where,
            include=["distances", "metadatas"] if return_metadata else ["distances"]
        )
        
        # Format results
        formatted_results = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted_results
        
        for i, result_id in enumerate(results['ids'][0]):
            distance = results['distances'][0][i]
            
            result = {
                "id": result_id,
                "distance": float(distance),
                "score": self._distance_to_score(float(distance))
            }
            
            if return_metadata and 'metadatas' in results:
                result["metadata"] = results['metadatas'][0][i]
            
            formatted_results.append(result)
        
        return formatted_results
    
    def search_batch(
        self,
        query_embeddings: np.ndarray,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        return_metadata: bool = True
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch search for similar vectors.
        
        Args:
            query_embeddings: Query vectors (2D array)
            k: Number of results per query
            where: Metadata filter
            return_metadata: Whether to include metadata
            
        Returns:
            List of result lists
        """
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=query_embeddings.tolist(),
            n_results=k,
            where=where,
            include=["distances", "metadatas"] if return_metadata else ["distances"]
        )
        
        # Format results for each query
        all_results = []
        
        for query_idx in range(len(query_embeddings)):
            query_results = []
            
            if results['ids'] and len(results['ids']) > query_idx:
                for i, result_id in enumerate(results['ids'][query_idx]):
                    distance = results['distances'][query_idx][i]
                    
                    result = {
                        "id": result_id,
                        "distance": float(distance),
                        "score": self._distance_to_score(float(distance))
                    }
                    
                    if return_metadata and 'metadatas' in results:
                        result["metadata"] = results['metadatas'][query_idx][i]
                    
                    query_results.append(result)
            
            all_results.append(query_results)
        
        return all_results
    
    def delete(self, ids: List[str]) -> int:
        """
        Delete vectors by IDs.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            self.collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} vectors from ChromaDB")
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return 0
    
    def update(
        self,
        ids: List[str],
        embeddings: Optional[np.ndarray] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Update vectors and/or metadata.
        
        Args:
            ids: List of vector IDs
            embeddings: New embeddings (optional)
            metadata: New metadata (optional)
        """
        update_kwargs = {"ids": ids}
        
        if embeddings is not None:
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            update_kwargs["embeddings"] = embeddings.tolist()
        
        if metadata is not None:
            update_kwargs["metadatas"] = metadata
        
        self.collection.update(**update_kwargs)
        logger.debug(f"Updated {len(ids)} vectors in ChromaDB")
    
    def clear(self):
        """Clear all vectors from collection"""
        # Delete collection and recreate
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"dimension": self.dimension}
        )
        logger.info(f"Cleared ChromaDB collection: {self.collection_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            "total_vectors": self.collection.count(),
            "dimension": self.dimension,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }
    
    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """Preview some vectors from the collection"""
        return self.collection.peek(limit=limit)
    
    @staticmethod
    def _distance_to_score(distance: float) -> float:
        """Convert distance to similarity score in [0, 1]"""
        # Smaller distance = higher similarity
        return 1.0 / (1.0 + distance)
    
    def __repr__(self) -> str:
        return (
            f"ChromaDBBackend(collection={self.collection_name}, "
            f"vectors={self.collection.count()}, dim={self.dimension})"
        )
