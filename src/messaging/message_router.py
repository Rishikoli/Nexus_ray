"""
Message router for intelligent Kafka topic routing.

Manages topic naming conventions and message routing patterns.
"""

from typing import Dict, Any, Optional
from enum import Enum
from loguru import logger


class TopicType(str, Enum):
    """Standard topic types in Nexus Ray"""
    
    WORKFLOW_EVENTS = "workflow.events"
    AGENT_INBOX = "agent.inbox"
    AGENT_BROADCAST = "agent.broadcast"
    METRICS_STREAM = "metrics.stream"
    LLM_ACTIVITY = "llm.activity"
    HITL_REQUESTS = "hitl.requests"


class MessageType(str, Enum):
    """Message types for routing"""
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Agent messages
    AGENT_MESSAGE = "agent_message"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    
    # LLM events
    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETED = "llm_call_completed"
    LLM_REASONING_TRACE = "llm_reasoning_trace"
    
    # HITL events
    HITL_APPROVAL_REQUIRED = "hitl_approval_required"
    HITL_APPROVED = "hitl_approved"
    HITL_REJECTED = "hitl_rejected"
    
    # Metrics
    METRIC_RECORDED = "metric_recorded"


class MessageRouter:
    """
    Routes messages to appropriate Kafka topics.
    
    Implements topic naming conventions and routing logic.
    """
    
    def __init__(self):
        logger.info("MessageRouter initialized")
    
    def get_workflow_events_topic(self) -> str:
        """Get topic for workflow lifecycle events"""
        return TopicType.WORKFLOW_EVENTS.value
    
    def get_agent_inbox_topic(self, agent_id: str) -> str:
        """
        Get inbox topic for a specific agent.
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            Topic name: agent.inbox.<agent_id>
        """
        return f"{TopicType.AGENT_INBOX.value}.{agent_id}"
    
    def get_agent_broadcast_topic(self) -> str:
        """Get topic for broadcasting to all agents"""
        return TopicType.AGENT_BROADCAST.value
    
    def get_metrics_topic(self) -> str:
        """Get topic for metrics streaming"""
        return TopicType.METRICS_STREAM.value
    
    def get_llm_activity_topic(self) -> str:
        """Get topic for LLM activity logging"""
        return TopicType.LLM_ACTIVITY.value
    
    def get_hitl_topic(self) -> str:
        """Get topic for HITL requests"""
        return TopicType.HITL_REQUESTS.value
    
    def route_message(self, message: Dict[str, Any]) -> str:
        """
        Determine the appropriate topic for a message.
        
        Args:
            message: Message to route
            
        Returns:
            Topic name
        """
        message_type = message.get('type')
        
        # Workflow events
        if message_type in [
            MessageType.WORKFLOW_STARTED,
            MessageType.WORKFLOW_COMPLETED,
            MessageType.WORKFLOW_FAILED,
            MessageType.TASK_STARTED,
            MessageType.TASK_COMPLETED,
            MessageType.TASK_FAILED
        ]:
            return self.get_workflow_events_topic()
        
        # Agent messages - route to specific inbox
        if message_type in [MessageType.AGENT_MESSAGE, MessageType.AGENT_REQUEST]:
            target_agent = message.get('target_agent')
            if target_agent:
                return self.get_agent_inbox_topic(target_agent)
            else:
                # Broadcast if no target
                return self.get_agent_broadcast_topic()
        
        # LLM events
        if message_type in [
            MessageType.LLM_CALL_STARTED,
            MessageType.LLM_CALL_COMPLETED,
            MessageType.LLM_REASONING_TRACE
        ]:
            return self.get_llm_activity_topic()
        
        # HITL events
        if message_type in [
            MessageType.HITL_APPROVAL_REQUIRED,
            MessageType.HITL_APPROVED,
            MessageType.HITL_REJECTED
        ]:
            return self.get_hitl_topic()
        
        # Metrics
        if message_type == MessageType.METRIC_RECORDED:
            return self.get_metrics_topic()
        
        # Default to broadcast
        logger.warning(f"Unknown message type {message_type}, routing to broadcast")
        return self.get_agent_broadcast_topic()
    
    def create_workflow_event(
        self,
        event_type: MessageType,
        workflow_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a workflow event message.
        
        Args:
            event_type: Type of workflow event
            workflow_id: Workflow identifier
            **kwargs: Additional event data
            
        Returns:
            Formatted message
        """
        return {
            'type': event_type.value,
            'workflow_id': workflow_id,
            **kwargs
        }
    
    def create_agent_message(
        self,
        from_agent: str,
        to_agent: Optional[str],
        content: Any,
        message_type: MessageType = MessageType.AGENT_MESSAGE,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create an agent-to-agent message.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID (None for broadcast)
            content: Message content
            message_type: Type of message
            **kwargs: Additional metadata
            
        Returns:
            Formatted message
        """
        message = {
            'type': message_type.value,
            'from_agent': from_agent,
            'content': content,
            **kwargs
        }
        
        if to_agent:
            message['target_agent'] = to_agent
        
        return message
    
    def create_llm_event(
        self,
        event_type: MessageType,
        agent_id: str,
        workflow_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create an LLM activity event.
        
        Args:
            event_type: Type of LLM event
            agent_id: Agent making the LLM call
            workflow_id: Associated workflow
            **kwargs: LLM call details (prompt, response, tokens, etc.)
            
        Returns:
            Formatted message
        """
        return {
            'type': event_type.value,
            'agent_id': agent_id,
            'workflow_id': workflow_id,
            **kwargs
        }
    
    def create_hitl_request(
        self,
        workflow_id: str,
        task_id: str,
        decision_data: Dict[str, Any],
        approvers: list,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a HITL approval request.
        
        Args:
            workflow_id: Workflow ID
            task_id: Task requiring approval
            decision_data: Data for human decision
            approvers: List of approvers
            **kwargs: Additional metadata
            
        Returns:
            Formatted message
        """
        return {
            'type': MessageType.HITL_APPROVAL_REQUIRED.value,
            'workflow_id': workflow_id,
            'task_id': task_id,
            'decision_data': decision_data,
            'approvers': approvers,
            **kwargs
        }
    
    def create_metric_event(
        self,
        metric_name: str,
        metric_value: float,
        labels: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a metrics event.
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            labels: Metric labels/dimensions
            **kwargs: Additional metadata
            
        Returns:
            Formatted message
        """
        return {
            'type': MessageType.METRIC_RECORDED.value,
            'metric_name': metric_name,
            'metric_value': metric_value,
            'labels': labels or {},
            **kwargs
        }
