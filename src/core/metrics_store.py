"""
Centralized store for system-wide metrics.
"""

from typing import Dict, Any, List
from threading import Lock
import time
import psutil
import os

class MetricsStore:
    """
    Singleton store for tracking real-time system metrics.
    Thread-safe implementation for concurrent agent execution.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsStore, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._lock = Lock()
        
        # LLM Metrics
        self.llm_calls_total: int = 0
        self.llm_input_tokens: int = 0
        self.llm_output_tokens: int = 0
        self.llm_errors: int = 0
        
        # Performance
        self.workflow_latencies: List[float] = []
        
        self._initialized = True
        
    def record_llm_call(self, input_tokens: int, output_tokens: int, success: bool = True):
        """Record a completed LLM call"""
        with self._lock:
            self.llm_calls_total += 1
            self.llm_input_tokens += input_tokens
            self.llm_output_tokens += output_tokens
            if not success:
                self.llm_errors += 1
                
    def record_latency(self, latency_seconds: float):
        """Record workflow execution latency"""
        with self._lock:
            self.workflow_latencies.append(latency_seconds)
            # Keep only last 1000 for memory efficiency
            if len(self.workflow_latencies) > 1000:
                self.workflow_latencies.pop(0)

    def get_llm_stats(self) -> Dict[str, Any]:
        """Get current LLM statistics"""
        with self._lock:
            return {
                "total_calls": self.llm_calls_total,
                "total_tokens": self.llm_input_tokens + self.llm_output_tokens,
                "input_tokens": self.llm_input_tokens,
                "output_tokens": self.llm_output_tokens,
                "errors": self.llm_errors
            }
            
    def get_avg_latency(self) -> float:
        """Get average latency"""
        with self._lock:
            if not self.workflow_latencies:
                return 0.0
            return sum(self.workflow_latencies) / len(self.workflow_latencies)

    def get_memory_usage(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

# Global Accessor
metrics_store = MetricsStore()
