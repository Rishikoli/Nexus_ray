"""
Multi-agent collaboration system.
"""

from src.collaboration.agent_registry import (
    AgentRegistry, AgentInfo, AgentCapability, AgentStatus, get_agent_registry
)
from src.collaboration.message_protocol import (
    AgentMessage, MessageType, MessageProtocol
)
from src.collaboration.coordinator import (
    CollaborationCoordinator, ConsensusStrategy, ConsensusResult,
    SharedContext, get_collaboration_coordinator
)

__all__ = [
    # Registry
    "AgentRegistry",
    "AgentInfo",
    "AgentCapability",
    "AgentStatus",
    "get_agent_registry",
    # Messages
    "AgentMessage",
    "MessageType",
    "MessageProtocol",
    # Coordinator
    "CollaborationCoordinator",
    "ConsensusStrategy",
    "ConsensusResult",
    "SharedContext",
    "get_collaboration_coordinator",
]
