"""
Metrics collection for Nexus Ray framework.

Provides Prometheus-compatible metrics for workflows, tasks, and LLM calls.
"""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import threading
from loguru import logger


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Base metric class"""
    name: str
    metric_type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """
    Collects and exposes Prometheus-compatible metrics.
    
    Thread-safe metrics collection for workflows, tasks, and LLM operations.
    """
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        
        logger.info("MetricsCollector initialized")
        
        # Initialize standard metrics
        self._init_standard_metrics()
    
    def _init_standard_metrics(self):
        """Initialize standard framework metrics"""
        # Workflow metrics
        self.register_counter("workflows_started_total", "Total workflows started")
        self.register_counter("workflows_completed_total", "Total workflows completed")
        self.register_counter("workflows_failed_total", "Total workflows failed")
        
        # Task metrics
        self.register_counter("tasks_executed_total", "Total tasks executed")
        self.register_counter("tasks_failed_total", "Total tasks failed")
        self.register_histogram("task_duration_seconds", "Task execution duration")
        
        # LLM metrics
        self.register_counter("llm_calls_total", "Total LLM calls")
        self.register_counter("llm_tokens_total", "Total tokens processed")
        self.register_histogram("llm_latency_seconds", "LLM call latency")
        
        # HITL metrics
        self.register_counter("hitl_requests_total", "Total HITL requests")
        self.register_gauge("hitl_pending", "Pending HITL approvals")
        
        logger.debug("Standard metrics initialized")
    
    def register_counter(self, name: str, description: str, labels: Optional[Dict] = None):
        """Register a counter metric"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._metrics[key] = Metric(
                name=name,
                metric_type=MetricType.COUNTER,
                description=description,
                labels=labels or {}
            )
    
    def register_gauge(self, name: str, description: str, labels: Optional[Dict] = None):
        """Register a gauge metric"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._metrics[key] = Metric(
                name=name,
                metric_type=MetricType.GAUGE,
                description=description,
                labels=labels or {}
            )
    
    def register_histogram(self, name: str, description: str, labels: Optional[Dict] = None):
        """Register a histogram metric"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._metrics[key] = Metric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                description=description,
                labels=labels or {}
            )
    
    def _get_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Get unique key for metric with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict] = None):
        """Increment a counter"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._counters[key] += value
            
            if key in self._metrics:
                self._metrics[key].value = self._counters[key]
                self._metrics[key].timestamp = datetime.utcnow()
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None):
        """Set a gauge value"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._gauges[key] = value
            
            if key in self._metrics:
                self._metrics[key].value = value
                self._metrics[key].timestamp = datetime.utcnow()
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict] = None):
        """Observe a value in a histogram"""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._histograms[key].append(value)
    
    def get_metric(self, name: str, labels: Optional[Dict] = None) -> Optional[Metric]:
        """Get a specific metric"""
        key = self._get_metric_key(name, labels or {})
        return self._metrics.get(key)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all collected metrics"""
        with self._lock:
            return dict(self._metrics)
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        with self._lock:
            for key, metric in self._metrics.items():
                # Help text
                lines.append(f"# HELP {metric.name} {metric.description}")
                lines.append(f"# TYPE {metric.name} {metric.metric_type.value}")
                
                # Metric value
                if metric.labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                    lines.append(f"{metric.name}{{{label_str}}} {metric.value}")
                else:
                    lines.append(f"{metric.name} {metric.value}")
                
                lines.append("")  # Blank line between metrics
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        with self._lock:
            return {
                "total_metrics": len(self._metrics),
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
                "metrics": {
                    name: {
                        "type": metric.metric_type.value,
                        "value": metric.value,
                        "labels": metric.labels
                    }
                    for name, metric in self._metrics.items()
                }
            }
    
    def reset(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._init_standard_metrics()
        
        logger.info("Metrics reset")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector


class WorkflowMetrics:
    """Helper for workflow-specific metrics"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.collector = get_metrics_collector()
        self.start_time: Optional[datetime] = None
    
    def workflow_started(self):
        """Record workflow start"""
        self.start_time = datetime.utcnow()
        self.collector.inc_counter("workflows_started_total", labels={"workflow_id": self.workflow_id})
    
    def workflow_completed(self):
        """Record workflow completion"""
        self.collector.inc_counter("workflows_completed_total", labels={"workflow_id": self.workflow_id})
        
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            self.collector.observe_histogram("workflow_duration_seconds", duration)
    
    def workflow_failed(self, error: str):
        """Record workflow failure"""
        self.collector.inc_counter("workflows_failed_total", labels={
            "workflow_id": self.workflow_id,
            "error_type": error
        })
    
    def task_executed(self, task_id: str, duration_ms: int, status: str):
        """Record task execution"""
        labels = {
            "workflow_id": self.workflow_id,
            "task_id": task_id,
            "status": status
        }
        
        self.collector.inc_counter("tasks_executed_total", labels=labels)
        self.collector.observe_histogram("task_duration_seconds", duration_ms / 1000.0)
        
        if status == "failed":
            self.collector.inc_counter("tasks_failed_total", labels=labels)
    
    def llm_call(self, model: str, input_tokens: int, output_tokens: int, latency_ms: int):
        """Record LLM call"""
        labels = {"model": model, "workflow_id": self.workflow_id}
        
        self.collector.inc_counter("llm_calls_total", labels=labels)
        self.collector.inc_counter("llm_tokens_total", value=input_tokens + output_tokens, labels=labels)
        self.collector.observe_histogram("llm_latency_seconds", latency_ms / 1000.0)
