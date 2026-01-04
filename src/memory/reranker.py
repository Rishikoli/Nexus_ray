"""
BGE Re-ranker with OpenVINO optimization.

Provides high-precision cross-encoder re-ranking for search results.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from pathlib import Path
from loguru import logger
import torch

try:
    from optimum.intel import OVModelForSequenceClassification
    from transformers import AutoTokenizer
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    logger.warning("OpenVINO not installed. BGE re-ranker will not be available.")

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError


class BGEReranker:
    """
    BGE Cross-Encoder Re-ranker with OpenVINO optimization.
    
    Features:
    - High-precision relevance scoring
    - OpenVINO INT8 quantization for speed
    - Accept pairs of (query, document)
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "CPU"
    ):
        """
        Initialize BGE re-ranker.
        
        Args:
            model_path: Path to OpenVINO model directory
            device: Device to use (CPU, GPU, etc.)
        """
        if not OPENVINO_AVAILABLE:
            raise EmbeddingError("OpenVINO not available - install optimum[openvino]")
        
        self.settings = get_settings()
        self.model_path = model_path or self._get_default_model_path()
        self.device = device
        self.model = None
        self.tokenizer = None
        
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default BGE model path from config or models directory"""
        # Check if model exists in models directory (using same base path strategy)
        # Note: In a real scenario, this might be a different model than the embedder
        # For this implementation, we assume a compatible re-ranker model is available
        # or we gracefully fallback/warn if specific re-ranker weights aren't found.
        
        default_path = Path("models/bge-reranker-v2-m3-ov")
        if default_path.exists():
            return str(default_path)
            
        # Fallback to the embedder path if specifically requested, 
        # though typically they are different models. 
        # Here we raise error to ensure correct model usage.
        raise EmbeddingError(
            f"BGE Re-ranker model not found at {default_path}. "
            "Please download the 'bge-reranker-v2-m3-ov' model."
        )
    
    def _load_model(self):
        """Load OpenVINO-optimized BGE re-ranker model"""
        try:
            logger.info(f"Loading BGE Re-ranker from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load OpenVINO model
            self.model = OVModelForSequenceClassification.from_pretrained(
                self.model_path,
                device=self.device
            )
            
            logger.info(f"✅ BGE Re-ranker loaded successfully on {self.device}")
            
        except Exception as e:
            # For now, just log error, don't crash app if optional component fails
            logger.error(f"Failed to load BGE Re-ranker: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank a list of documents based on relevance to the query.
        
        Args:
            query: The search query
            documents: List of candidate documents
            top_k: Number of top results to return
            
        Returns:
            List of dicts with {'text': str, 'score': float, 'index': int}
            sorted by score descending.
        """
        if not self.model:
            logger.warning("Re-ranker model not loaded. Returning original order.")
            return [
                {"text": doc, "score": 0.0, "index": i} 
                for i, doc in enumerate(documents)
            ][:top_k]
            
        if not documents:
            return []
            
        try:
            # Prepare pairs
            pairs = [[query, doc] for doc in documents]
            
            # Tokenize
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                if logits.shape[1] == 1:
                    scores = logits.view(-1).float()
                else:
                    scores = logits[:, 1].float() # Assuming label 1 is "relevant"
            
            # Sigmoid/Normalize scores if needed (BGE-reranker usually outputs raw logits)
            # For BGE, logits are directly usable as scores. Higher is better.
            scores = scores.numpy()
            
            # Create qualified results
            results = []
            for i, score in enumerate(scores):
                results.append({
                    "text": documents[i],
                    "score": float(score),
                    "index": i
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)
            
            if top_k:
                results = results[:top_k]
                
            return results
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            # Fallback to original order
            return [
                {"text": doc, "score": 0.0, "index": i} 
                for i, doc in enumerate(documents)
            ][:top_k]


# Singleton instance
_reranker: Optional[BGEReranker] = None

def get_reranker() -> BGEReranker:
    """Get global BGE re-ranker instance"""
    global _reranker
    if _reranker is None:
        try:
            _reranker = BGEReranker()
        except Exception as e:
            logger.warning(f"Could not initialize global re-ranker: {e}")
            _reranker = None
    return _reranker
