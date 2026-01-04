"""
Activity feed system for real-time workflow and task events.

Provides a stream of events for monitoring and debugging.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import deque
import threading
from loguru import logger


class ActivityType(str, Enum):
    """Types of activities"""
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    
    # LLM events
    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETED = "llm_call_completed"
    LLM_CALL_FAILED = "llm_call_failed"
    
    # HITL events
    HITL_REQUESTED = "hitl_requested"
    HITL_APPROVED = "hitl_approved"
    HITL_REJECTED = "hitl_rejected"
    
    # System events
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"


@dataclass
class Activity:
    """Single activity record"""
    activity_id: str
    activity_type: ActivityType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Content
    title: str = ""
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    severity: str = "info"  # info, warning, error
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['activity_type'] = self.activity_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    def to_json_serializable(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return self.to_dict()


class ActivityFeed:
    """
    Real-time activity feed for monitoring.
    
    Maintains a rolling buffer of recent activities and supports
    subscriptions for real-time updates.
    """
    
    def __init__(self, max_activities: int = 1000):
        self.max_activities = max_activities
        self.activities: deque = deque(maxlen=max_activities)
        self.subscribers: List[Callable[[Activity], None]] = []
        self._lock = threading.Lock()
        self._activity_counter = 0
        
        logger.info(f"ActivityFeed initialized (max={max_activities})")
    
    def _generate_activity_id(self) -> str:
        """Generate unique activity ID"""
        with self._lock:
            self._activity_counter += 1
            return f"activity-{self._activity_counter}"
    
    def add_activity(
        self,
        activity_type: ActivityType,
        title: str,
        description: str = "",
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        data: Optional[Dict] = None,
        severity: str = "info",
        tags: Optional[List[str]] = None
    ) -> Activity:
        """Add a new activity to the feed"""
        activity = Activity(
            activity_id=self._generate_activity_id(),
            activity_type=activity_type,
            title=title,
            description=description,
            workflow_id=workflow_id,
            task_id=task_id,
            data=data or {},
            severity=severity,
            tags=tags or []
        )
        
        with self._lock:
            self.activities.append(activity)
        
        # Notify subscribers
        self._notify_subscribers(activity)
        
        logger.debug(f"Activity added: {activity.title}")
        return activity
    
    def _notify_subscribers(self, activity: Activity):
        """Notify all subscribers of new activity"""
        for subscriber in self.subscribers:
            try:
                subscriber(activity)
            except Exception as e:
                logger.error(f"Subscriber notification failed: {e}")
    
    def subscribe(self, callback: Callable[[Activity], None]):
        """Subscribe to activity feed"""
        with self._lock:
            self.subscribers.append(callback)
        logger.debug(f"Subscriber added (total: {len(self.subscribers)})")
    
    def unsubscribe(self, callback: Callable[[Activity], None]):
        """Unsubscribe from activity feed"""
        with self._lock:
            if callback in self.subscribers:
                self.subscribers.remove(callback)
        logger.debug(f"Subscriber removed (total: {len(self.subscribers)})")
    
    def get_recent(self, limit: int = 50) -> List[Activity]:
        """Get recent activities"""
        with self._lock:
            activities = list(self.activities)
        
        # Return most recent first
        return list(reversed(activities[-limit:]))
    
    def get_for_workflow(self, workflow_id: str, limit: int = 100) -> List[Activity]:
        """Get activities for a specific workflow"""
        with self._lock:
            activities = [
                a for a in self.activities
                if a.workflow_id == workflow_id
            ]
        
        return list(reversed(activities[-limit:]))
    
    def get_by_type(self, activity_type: ActivityType, limit: int = 50) -> List[Activity]:
        """Get activities by type"""
        with self._lock:
            activities = [
                a for a in self.activities
                if a.activity_type == activity_type
            ]
        
        return list(reversed(activities[-limit:]))
    
    def get_errors(self, limit: int = 50) -> List[Activity]:
        """Get error activities"""
        with self._lock:
            activities = [
                a for a in self.activities
                if a.severity == "error"
            ]
        
        return list(reversed(activities[-limit:]))
    
    def clear(self):
        """Clear all activities"""
        with self._lock:
            self.activities.clear()
        logger.info("Activity feed cleared")
    
    def export(self, limit: Optional[int] = None) -> List[Dict]:
        """Export activities as JSON-serializable dicts"""
        activities = self.get_recent(limit or len(self.activities))
        return [a.to_dict() for a in activities]


class WorkflowActivityTracker:
    """Helper for tracking workflow-specific activities"""
    
    def __init__(self, workflow_id: str, feed: Optional[ActivityFeed] = None):
        self.workflow_id = workflow_id
        self.feed = feed or get_activity_feed()
    
    def workflow_started(self, workflow_name: str, tasks_count: int):
        """Record workflow start"""
        self.feed.add_activity(
            activity_type=ActivityType.WORKFLOW_STARTED,
            title=f"Workflow started: {workflow_name}",
            description=f"Starting workflow with {tasks_count} tasks",
            workflow_id=self.workflow_id,
            data={"workflow_name": workflow_name, "tasks_count": tasks_count},
            severity="info",
            tags=["workflow", "start"]
        )
    
    def workflow_completed(self, duration_seconds: float):
        """Record workflow completion"""
        self.feed.add_activity(
            activity_type=ActivityType.WORKFLOW_COMPLETED,
            title="Workflow completed successfully",
            description=f"Completed in {duration_seconds:.2f}s",
            workflow_id=self.workflow_id,
            data={"duration_seconds": duration_seconds},
            severity="info",
            tags=["workflow", "success"]
        )
    
    def workflow_failed(self, error: str):
        """Record workflow failure"""
        self.feed.add_activity(
            activity_type=ActivityType.WORKFLOW_FAILED,
            title="Workflow failed",
            description=error,
            workflow_id=self.workflow_id,
            data={"error": error},
            severity="error",
            tags=["workflow", "error"]
        )
    
    def task_started(self, task_id: str, task_name: str):
        """Record task start"""
        self.feed.add_activity(
            activity_type=ActivityType.TASK_STARTED,
            title=f"Task started: {task_name}",
            workflow_id=self.workflow_id,
            task_id=task_id,
            data={"task_name": task_name},
            tags=["task", "start"]
        )
    
    def task_completed(self, task_id: str, task_name: str, duration_ms: int):
        """Record task completion"""
        self.feed.add_activity(
            activity_type=ActivityType.TASK_COMPLETED,
            title=f"Task completed: {task_name}",
            description=f"Completed in {duration_ms}ms",
            workflow_id=self.workflow_id,
            task_id=task_id,
            data={"task_name": task_name, "duration_ms": duration_ms},
            tags=["task", "success"]
        )
    
    def task_failed(self, task_id: str, task_name: str, error: str):
        """Record task failure"""
        self.feed.add_activity(
            activity_type=ActivityType.TASK_FAILED,
            title=f"Task failed: {task_name}",
            description=error,
            workflow_id=self.workflow_id,
            task_id=task_id,
            data={"task_name": task_name, "error": error},
            severity="error",
            tags=["task", "error"]
        )
    
    def llm_call(self, task_id: str, model: str, tokens: int):
        """Record LLM call"""
        self.feed.add_activity(
            activity_type=ActivityType.LLM_CALL_COMPLETED,
            title=f"LLM call: {model}",
            description=f"Used {tokens} tokens",
            workflow_id=self.workflow_id,
            task_id=task_id,
            data={"model": model, "tokens": tokens},
            tags=["llm"]
        )
    
    def hitl_requested(self, task_id: str, approvers: List[str]):
        """Record HITL request"""
        self.feed.add_activity(
            activity_type=ActivityType.HITL_REQUESTED,
            title="Human approval required",
            description=f"Waiting for approval from {', '.join(approvers)}",
            workflow_id=self.workflow_id,
            task_id=task_id,
            data={"approvers": approvers},
            severity="warning",
            tags=["hitl", "pending"]
        )


# Global activity feed instance
_activity_feed: Optional[ActivityFeed] = None


def get_activity_feed() -> ActivityFeed:
    """Get or create global activity feed"""
    global _activity_feed
    
    if _activity_feed is None:
        _activity_feed = ActivityFeed()
    
    return _activity_feed
