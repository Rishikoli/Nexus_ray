"""
Task definitions and schemas for Nexus Ray workflows.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Type of task executor"""
    LLM = "llm"
    TOOL = "tool"
    HUMAN = "human"  # HITL tasks
    AGENT = "agent"  # Custom agent


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING_HUMAN = "waiting_human"
    CANCELLED = "cancelled"


class TaskDefinition(BaseModel):
    """Definition of a single task in a workflow"""
    
    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    task_type: TaskType = Field(..., description="Type of executor to use")
    
    # Execution configuration
    executor_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for the executor"
    )
    
    # Dependencies
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task_ids that must complete before this task"
    )
    
    # Input/Output
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data for the task"
    )
    
    # Retry and timeout
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(
        default=None,
        description="Task timeout in seconds"
    )
    
    # HITL configuration
    hitl_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Human-in-the-loop configuration"
    )
    
    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    """Result of a task execution"""
    
    task_id: str
    status: TaskStatus
    
    # Outputs
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific metrics (tokens, latency, etc.)"
    )
    
    # Retry information
    retry_count: int = 0
    
    class Config:
        use_enum_values = True
    
    @property
    def is_complete(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status in [
            TaskStatus.SUCCESS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ]
    
    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.status == TaskStatus.SUCCESS


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    
    workflow_id: str
    name: str
    description: Optional[str] = None
    
    tasks: List[TaskDefinition]
    
    # Workflow-level configuration
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
