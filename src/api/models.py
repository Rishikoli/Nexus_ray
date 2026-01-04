"""
Pydantic models for API requests and responses.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# Workflow Models
class WorkflowCreateRequest(BaseModel):
    """Request to create a workflow"""
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = None
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks")
    

class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow"""
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    

class WorkflowResponse(BaseModel):
    """Workflow response"""
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    tasks: List[Dict[str, Any]]
    

class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response"""
    execution_id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    

# Agent Models
class AgentRegisterRequest(BaseModel):
    """Request to register an agent"""
    agent_id: str
    name: str
    capabilities: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    

class AgentResponse(BaseModel):
    """Agent response"""
    agent_id: str
    name: str
    capabilities: List[str]
    status: str
    current_tasks: int
    max_concurrent_tasks: int
    

# LLM Models
class LLMGenerateRequest(BaseModel):
    """Request to generate text"""
    prompt: str = Field(..., description="Prompt text")
    max_tokens: int = Field(default=300, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    

class LLMGenerateResponse(BaseModel):
    """LLM generation response"""
    text: str
    tokens_used: int
    latency: float
    model: str
    

# Metrics Models
class MetricsResponse(BaseModel):
    """Metrics response"""
    total_workflows: int
    active_workflows: int
    total_agents: int
    available_agents: int
    llm_calls_total: int
    llm_tokens_total: int
    

# Collaboration Models
class ConsensusRequest(BaseModel):
    """Request to start consensus"""
    question: str
    options: List[Any]
    strategy: str = Field(default="majority_vote")
    from_agent: str
    

class ConsensusResponse(BaseModel):
    """Consensus response"""
    correlation_id: str
    question: str
    winning_option: Optional[Any]
    votes: Dict[str, Any]
    confidence: float
    

# Guardrails Models
class ContentFilterRequest(BaseModel):
    """Request to filter content"""
    text: str
    strict_mode: bool = Field(default=False)
    

class ContentFilterResponse(BaseModel):
    """Content filter response"""
    passed: bool
    blocked_categories: List[str]
    sanitized_text: str
    confidence: float
    

class SafetyScoreResponse(BaseModel):
    """Safety score response"""
    level: str
    score: float
    categories: Dict[str, float]
    recommendations: List[str]
