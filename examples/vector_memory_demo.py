"""
Vector memory demonstration.

Shows how to use the memory system for semantic search.
"""

import asyncio
import numpy as np
from loguru import logger

from src.memory import VectorMemory, get_vector_memory, VectorBackendType


def demo_basic_usage():
    """Demonstrate basic vector memory usage"""
    print("=" * 80)
    print("Vector Memory - Basic Usage Demo")
    print("=" * 80)
    print()
    
    # Create memory (FAISS backend for speed)
    logger.info("Creating vector memory with FAISS backend...")
    memory = VectorMemory(backend=VectorBackendType.FAISS)
    
    # Sample documents
    documents = [
        "Machine learning is a subset of artificial intelligence",
        "Neural networks are used for deep learning",
        "Python is a popular programming language",
        "OpenVINO optimizes AI models for Intel hardware",
        "Vector databases enable semantic search",
        "Embeddings represent text as numerical vectors",
        "FAISS provides fast similarity search",
        "ChromaDB offers persistent vector storage"
    ]
    
    # Add documents to memory
    logger.info(f"Adding {len(documents)} documents to memory...")
    ids = memory.add_texts(documents)
    logger.info(f"✅ Added documents with IDs: {ids[:3]}...")
    print()
    
    # Search
    queries = [
        "What is machine learning?",
        "Tell me about vector databases",
        "How can I optimize AI models?"
    ]
    
    for query in queries:
        logger.info(f"Query: '{query}'")
        results = memory.search(query, k=3)
        
        print(f"\nTop {len(results)} results:")
        for i, result in enumerate(results, 1):
            doc_id = result['id']
            score = result['score']
            print(f"  {i}. [Score: {score:.3f}] {documents[doc_id]}")
        print()
    
    # Stats
    stats = memory.get_stats()
    logger.info(f"Memory stats: {stats}")
    print()


def demo_with_metadata():
    """Demonstrate memory with metadata filtering"""
    print("=" * 80)
    print("Vector Memory - Metadata Demo")
    print("=" * 80)
    print()
    
    # Create ChromaDB backend (supports metadata filtering)
    logger.info("Creating vector memory with ChromaDB backend...")
    memory = VectorMemory(backend=VectorBackendType.CHROMADB)
    
    # Clear previous data
    memory.clear()
    
    # Documents with metadata
    documents = [
        ("Python tutorials for beginners", {"type": "tutorial", "language": "python", "level": "beginner"}),
        ("Advanced Python programming techniques", {"type": "tutorial", "language": "python", "level": "advanced"}),
        ("JavaScript basics and fundamentals", {"type": "tutorial", "language": "javascript", "level": "beginner"}),
        ("Machine learning with Python", {"type": "guide", "language": "python", "topic": "ml"}),
        ("Deep learning frameworks comparison", {"type": "guide", "topic": "ml"}),
    ]
    
    texts = [doc[0] for doc in documents]
    metadata = [doc[1] for doc in documents]
    
    # Add with metadata
    logger.info(f"Adding {len(documents)} documents with metadata...")
    ids = memory.add_texts(texts, metadata=metadata)
    logger.info(f"✅ Added documents")
    print()
    
    # Search with metadata filter
    query = "programming tutorials"
    
    logger.info(f"Query: '{query}' (all documents)")
    results = memory.search(query, k=3)
    print("Results (no filter):")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('metadata', {})}")
    print()
    
    logger.info(f"Query: '{query}' (filter: type=tutorial, level=beginner)")
    results = memory.search(query, k=3, where={"$and": [{"type": "tutorial"}, {"level": "beginner"}]})
    print("Results (with filter):")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('metadata', {})}")
    print()


def demo_embeddings_direct():
    """Demonstrate using embeddings directly"""
    print("=" * 80)
    print("Vector Memory - Direct Embeddings Demo")
    print("=" * 80)
    print()
    
    from src.memory import get_embedder
    
    # Get embedder
    embedder = get_embedder()
    logger.info(f"Loaded embedder: {embedder}")
    print()
    
    # Generate embeddings
    texts = [
        "artificial intelligence",
        "machine learning",
        "banana fruit"
    ]
    
    logger.info(f"Generating embeddings for {len(texts)} texts...")
    embeddings = embedder.embed(texts)
    logger.info(f"✅ Generated embeddings: shape={embeddings.shape}")
    print()
    
    # Compute similarities
    logger.info("Computing pairwise similarities...")
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            sim = embedder.similarity(texts[i], texts[j])
            print(f"  '{texts[i]}' <-> '{texts[j]}': {sim:.3f}")
    print()


def demo_singleton():
    """Demonstrate singleton memory instances"""
    print("=" * 80)
    print("Vector Memory - Singleton Demo")
    print("=" * 80)
    print()
    
    # Get named memories
    logger.info("Creating named memory instances...")
    
    memory1 = get_vector_memory("agent1", backend="faiss")
    memory2 = get_vector_memory("agent2", backend="faiss")
    memory1_again = get_vector_memory("agent1")  # Same instance
    
    # Add different data to each
    memory1.add_texts(["Agent 1 knowledge base"])
    memory2.add_texts(["Agent 2 knowledge base"])
    
    print(f"Memory 1: {memory1}")
    print(f"Memory 2: {memory2}")
    print(f"Memory 1 (again): {memory1_again}")
    print(f"Same instance? {memory1 is memory1_again}")
    print()


def main():
    """Run all demos"""
    try:
        demo_basic_usage()
        demo_with_metadata()
        demo_embeddings_direct()
        demo_singleton()
        
        logger.info("✅ All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
