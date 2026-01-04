"""
LLM insights tracking and analytics.

Captures reasoning traces, token usage, and performance metrics for LLM calls.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
from loguru import logger


class LLMProvider(str, Enum):
    """LLM provider types"""
    OPENVINO = "openvino"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class TokenUsage:
    """Token usage tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class LLMCall:
    """Single LLM call record"""
    call_id: str
    workflow_id: str
    task_id: str
    model: str
    provider: LLMProvider
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Content
    prompt: str = ""
    response: str = ""
    system_prompt: Optional[str] = None
    
    # Usage
    tokens: TokenUsage = field(default_factory=TokenUsage)
    
    # Parameters
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 1.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def calculate_duration(self):
        """Calculate duration if both timestamps available"""
        if self.completed_at and self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['provider'] = self.provider.value
        data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class ReasoningTrace:
    """LLM reasoning trace for explainability"""
    trace_id: str
    llm_call_id: str
    workflow_id: str
    task_id: str
    
    # Reasoning steps
    thought_process: List[str] = field(default_factory=list)
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
    final_reasoning: str = ""
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, description: str, data: Optional[Dict] = None):
        """Add reasoning step"""
        self.thought_process.append(description)
        if data:
            self.intermediate_steps.append({
                "step": len(self.thought_process),
                "description": description,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "llm_call_id": self.llm_call_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "thought_process": self.thought_process,
            "intermediate_steps": self.intermediate_steps,
            "final_reasoning": self.final_reasoning,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class LLMInsightsTracker:
    """
    Tracks LLM calls and reasoning for analytics and debugging.
    
    Provides insights into:
    - Token usage and costs
    - LLM performance
    - Reasoning traces
    - Error patterns
    """
    
    def __init__(self):
        self.llm_calls: Dict[str, LLMCall] = {}
        self.reasoning_traces: Dict[str, ReasoningTrace] = {}
        
        # Aggregated stats
        self.total_calls = 0
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        
        # Cost per 1K tokens (can be configured)
        self.cost_per_1k_tokens = {
            "mistral-7b-ov": 0.0,  # Free/local
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.03,
            "claude-3-sonnet": 0.015
        }
        
        logger.info("LLMInsightsTracker initialized")
    
    def track_call(self, llm_call: LLMCall):
        """Track an LLM call"""
        self.llm_calls[llm_call.call_id] = llm_call
        
        # Update aggregated stats
        self.total_calls += 1
        self.total_tokens += llm_call.tokens.total_tokens
        
        # Estimate cost
        model_name = llm_call.model
        if model_name in self.cost_per_1k_tokens:
            cost_per_1k = self.cost_per_1k_tokens[model_name]
            call_cost = (llm_call.tokens.total_tokens / 1000.0) * cost_per_1k
            self.total_cost_usd += call_cost
        
        logger.debug(f"Tracked LLM call: {llm_call.call_id} ({llm_call.tokens.total_tokens} tokens)")
    
    def track_reasoning(self, trace: ReasoningTrace):
        """Track a reasoning trace"""
        self.reasoning_traces[trace.trace_id] = trace
        logger.debug(f"Tracked reasoning trace: {trace.trace_id}")
    
    def get_call(self, call_id: str) -> Optional[LLMCall]:
        """Get specific LLM call"""
        return self.llm_calls.get(call_id)
    
    def get_calls_for_workflow(self, workflow_id: str) -> List[LLMCall]:
        """Get all LLM calls for a workflow"""
        return [
            call for call in self.llm_calls.values()
            if call.workflow_id == workflow_id
        ]
    
    def get_reasoning_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Get specific reasoning trace"""
        return self.reasoning_traces.get(trace_id)
    
    def get_workflow_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """Get analytics for a specific workflow"""
        calls = self.get_calls_for_workflow(workflow_id)
        
        if not calls:
            return {"error": "No LLM calls found for workflow"}
        
        total_tokens = sum(call.tokens.total_tokens for call in calls)
        avg_duration = sum(call.duration_ms or 0 for call in calls) / len(calls)
        
        # Token breakdown
        input_tokens = sum(call.tokens.input_tokens for call in calls)
        output_tokens = sum(call.tokens.output_tokens for call in calls)
        
        # Model distribution
        models = {}
        for call in calls:
            models[call.model] = models.get(call.model, 0) + 1
        
        return {
            "workflow_id": workflow_id,
            "total_calls": len(calls),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "avg_duration_ms": avg_duration,
            "models_used": models,
            "errors": len([c for c in calls if c.error])
        }
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """Get global LLM analytics"""
        if not self.llm_calls:
            return {"total_calls": 0, "total_tokens": 0}
        
        # Model performance
        model_stats = {}
        for call in self.llm_calls.values():
            if call.model not in model_stats:
                model_stats[call.model] = {
                    "calls": 0,
                    "tokens": 0,
                    "avg_duration_ms": 0,
                    "errors": 0
                }
            
            stats = model_stats[call.model]
            stats["calls"] += 1
            stats["tokens"] += call.tokens.total_tokens
            stats["avg_duration_ms"] += call.duration_ms or 0
            if call.error:
                stats["errors"] += 1
        
        # Calculate averages
        for model, stats in model_stats.items():
            if stats["calls"] > 0:
                stats["avg_duration_ms"] /= stats["calls"]
        
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.total_cost_usd, 4),
            "model_stats": model_stats,
            "total_reasoning_traces": len(self.reasoning_traces)
        }
    
    def export_traces(self, workflow_id: Optional[str] = None) -> List[Dict]:
        """Export reasoning traces"""
        traces = self.reasoning_traces.values()
        
        if workflow_id:
            traces = [t for t in traces if t.workflow_id == workflow_id]
        
        return [trace.to_dict() for trace in traces]
    
    def export_calls(self, workflow_id: Optional[str] = None) -> List[Dict]:
        """Export LLM calls"""
        calls = self.llm_calls.values()
        
        if workflow_id:
            calls = [c for c in calls if c.workflow_id == workflow_id]
        
        return [call.to_dict() for call in calls]
    
    def reset(self):
        """Reset all tracking data"""
        self.llm_calls.clear()
        self.reasoning_traces.clear()
        self.total_calls = 0
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        
        logger.info("LLM insights tracker reset")


# Global tracker instance
_llm_tracker: Optional[LLMInsightsTracker] = None


def get_llm_tracker() -> LLMInsightsTracker:
    """Get or create global LLM insights tracker"""
    global _llm_tracker
    
    if _llm_tracker is None:
        _llm_tracker = LLMInsightsTracker()
    
    return _llm_tracker
