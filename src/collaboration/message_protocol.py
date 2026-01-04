"""
Message protocol for agent-to-agent communication.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid


class MessageType(str, Enum):
    """Types of agent messages"""
    # Request/Response
    REQUEST = "request"
    RESPONSE = "response"
    
    # Collaboration
    TASK_PROPOSAL = "task_proposal"
    TASK_ACCEPTANCE = "task_acceptance"
    TASK_REJECTION = "task_rejection"
    
    # Information sharing
    CONTEXT_SHARE = "context_share"
    RESULT_SHARE = "result_share"
    
    # Coordination
    CONSENSUS_REQUEST = "consensus_request"
    VOTE = "vote"
    COORDINATION_UPDATE = "coordination_update"
    
    # Status
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"


@dataclass
class AgentMessage:
    """Message between agents"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    
    # Routing
    from_agent: str = ""
    to_agent: Optional[str] = None  # None = broadcast
    
    # Content
    content: Dict[str, Any] = field(default_factory=dict)
    payload: Any = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None  # For responses
    correlation_id: Optional[str] = None  # For tracking conversations
    
    # Priority & TTL
    priority: int = 5  # 1-10, higher = more important
    ttl_seconds: int = 300  # Time to live
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def is_broadcast(self) -> bool:
        """Check if message is broadcast"""
        return self.to_agent is None
    
    def is_response(self) -> bool:
        """Check if message is a response"""
        return self.reply_to is not None


class MessageProtocol:
    """
    Protocol for agent-to-agent messages.
    
    Provides helper methods for creating standard message types.
    """
    
    @staticmethod
    def create_request(
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> AgentMessage:
        """Create a request message"""
        return AgentMessage(
            message_type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
    
    @staticmethod
    def create_response(
        from_agent: str,
        to_agent: str,
        original_message: AgentMessage,
        content: Dict[str, Any]
    ) -> AgentMessage:
        """Create a response message"""
        return AgentMessage(
            message_type=MessageType.RESPONSE,
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            reply_to=original_message.message_id,
            correlation_id=original_message.correlation_id
        )
    
    @staticmethod
    def create_task_proposal(
        from_agent: str,
        to_agent: str,
        task_description: str,
        task_data: Dict[str, Any]
    ) -> AgentMessage:
        """Create a task proposal"""
        return AgentMessage(
            message_type=MessageType.TASK_PROPOSAL,
            from_agent=from_agent,
            to_agent=to_agent,
            content={
                "description": task_description,
                "task_data": task_data
            }
        )
    
    @staticmethod
    def create_consensus_request(
        from_agent: str,
        question: str,
        options: List[Any],
        context: Optional[Dict] = None
    ) -> AgentMessage:
        """Create a consensus request (broadcast)"""
        return AgentMessage(
            message_type=MessageType.CONSENSUS_REQUEST,
            from_agent=from_agent,
            to_agent=None,  # Broadcast
            content={
                "question": question,
                "options": options,
                "context": context or {}
            },
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_vote(
        from_agent: str,
        to_agent: str,
        consensus_message: AgentMessage,
        vote: Any,
        reasoning: Optional[str] = None
    ) -> AgentMessage:
        """Create a vote response"""
        return AgentMessage(
            message_type=MessageType.VOTE,
            from_agent=from_agent,
            to_agent=to_agent,
            content={
                "vote": vote,
                "reasoning": reasoning
            },
            reply_to=consensus_message.message_id,
            correlation_id=consensus_message.correlation_id
        )
    
    @staticmethod
    def create_context_share(
        from_agent: str,
        context_key: str,
        context_data: Any
    ) -> AgentMessage:
        """Create a context sharing message (broadcast)"""
        return AgentMessage(
            message_type=MessageType.CONTEXT_SHARE,
            from_agent=from_agent,
            to_agent=None,  # Broadcast
            content={
                "key": context_key,
                "data": context_data
            }
        )
    
    @staticmethod
    def create_result_share(
        from_agent: str,
        result_type: str,
        result_data: Any
    ) -> AgentMessage:
        """Create a result sharing message"""
        return AgentMessage(
            message_type=MessageType.RESULT_SHARE,
            from_agent=from_agent,
            to_agent=None,  # Broadcast
            content={
                "result_type": result_type,
                "result": result_data
            }
        )
