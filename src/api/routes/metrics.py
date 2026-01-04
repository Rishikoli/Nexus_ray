"""
Metrics API routes.

Provides real-time system metrics, activity feeds, and LLM usage stats.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
import time
import random 

# Import shared state
from src.api.routes.reference_agents import workflow_results
from src.api.routes.hitl import hitl_store
from src.core.metrics_store import metrics_store

router = APIRouter()

class SystemMetrics(BaseModel):
    total_workflows: int
    active_workflows: int
    total_agents: int
    available_agents: int
    llm_calls_total: int
    llm_tokens_total: int
    avg_latency: float
    success_rate: float
    memory_usage: float
    hitl_pending: int

class ActivityEvent(BaseModel):
    type: str
    timestamp: float
    details: Dict[str, Any]

class ActivityFeed(BaseModel):
    events: List[ActivityEvent]

class LLMInsights(BaseModel):
    total_calls: int
    total_tokens: int
    avg_latency: float
    cost_estimate: float
    top_prompts: List[str]

@router.get("", response_model=SystemMetrics)
async def get_metrics():
    """
    Get real-time system metrics based on actual workflow execution data.
    """
    total = len(workflow_results)
    # Count active (not complete or failed)
    active = sum(1 for w in workflow_results.values() if w["status"] not in ["complete", "failed"])
    
    # Calculate success rate
    completed = sum(1 for w in workflow_results.values() if w["status"] == "complete")
    success_rate = (completed / total * 100) if total > 0 else 100.0
    
    # Get stats from central store
    llm_stats = metrics_store.get_llm_stats()
    
    # Simple cost estimate ($0.15 / 1M tokens)
    # This is a mock rate for demonstration
    
    # Count TOTAL HITL requests (Cumulative history)
    total_hitl = len(hitl_store)

    return SystemMetrics(
        total_workflows=total,
        active_workflows=active,
        total_agents=14, # 7 protein + 7 semiconductor
        available_agents=14 if active < 5 else max(0, 14 - active * 2), # Simulate utilization
        llm_calls_total=llm_stats["total_calls"],
        llm_tokens_total=llm_stats["total_tokens"],
        avg_latency=metrics_store.get_avg_latency(),
        success_rate=success_rate if total > 0 else 0.0,
        memory_usage=metrics_store.get_memory_usage(),
        hitl_pending=total_hitl
    )

@router.get("/activity", response_model=ActivityFeed)
async def get_activity():
    """Returns recent activity feed."""
    return ActivityFeed(events=[])

@router.get("/llm", response_model=LLMInsights)
async def get_llm_insights():
    """Returns LLM specific metrics."""
    stats = metrics_store.get_llm_stats()
    
    # Mock cost calculation
    cost = (stats["total_tokens"] / 1000000) * 0.15
    
    return LLMInsights(
        total_calls=stats["total_calls"],
        total_tokens=stats["total_tokens"],
        avg_latency=0.0, # Not tracked per-call yet
        cost_estimate=cost,
        top_prompts=[]
    )
