"""
Agent registry for multi-agent collaboration.

Manages agent discovery, registration, and capabilities.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class AgentCapability(str, Enum):
    """Agent capability types"""
    LLM_ANALYSIS = "llm_analysis"
    DATA_PROCESSING = "data_processing"
    TOOL_EXECUTION = "tool_execution"
    DECISION_MAKING = "decision_making"
    VALIDATION = "validation"
    COORDINATION = "coordination"


class AgentStatus(str, Enum):
    """Agent status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Information about a registered agent"""
    agent_id: str
    name: str
    capabilities: Set[AgentCapability]
    status: AgentStatus = AgentStatus.AVAILABLE
    metadata: Dict = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    
    # Load tracking
    current_tasks: int = 0
    max_concurrent_tasks: int = 5
    
    def is_available(self) -> bool:
        """Check if agent is available for work"""
        return (
            self.status == AgentStatus.AVAILABLE and
            self.current_tasks < self.max_concurrent_tasks
        )
    
    def can_handle(self, capability: AgentCapability) -> bool:
        """Check if agent has required capability"""
        return capability in self.capabilities


class AgentRegistry:
    """
    Registry for discovering and managing agents.
    
    Features:
    - Agent registration and discovery
    - Capability-based agent selection
    - Load balancing
    - Health monitoring
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self._lock = threading.Lock()
    
    def register(
        self,
        agent_id: str,
        name: str,
        capabilities: List[AgentCapability],
        metadata: Optional[Dict] = None
    ) -> AgentInfo:
        """
        Register a new agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            capabilities: List of agent capabilities
            metadata: Additional metadata
            
        Returns:
            AgentInfo object
        """
        with self._lock:
            agent_info = AgentInfo(
                agent_id=agent_id,
                name=name,
                capabilities=set(capabilities),
                metadata=metadata or {}
            )
            self.agents[agent_id] = agent_info
            return agent_info
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent"""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                return True
            return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent info by ID"""
        return self.agents.get(agent_id)
    
    def find_agents_by_capability(
        self,
        capability: AgentCapability,
        only_available: bool = True
    ) -> List[AgentInfo]:
        """
        Find agents with specific capability.
        
        Args:
            capability: Required capability
            only_available: Only return available agents
            
        Returns:
            List of matching agents
        """
        with self._lock:
            agents = [
                agent for agent in self.agents.values()
                if agent.can_handle(capability)
            ]
            
            if only_available:
                agents = [a for a in agents if a.is_available()]
            
            # Sort by load (least loaded first)
            agents.sort(key=lambda a: a.current_tasks)
            
            return agents
    
    def select_best_agent(
        self,
        required_capabilities: List[AgentCapability]
    ) -> Optional[AgentInfo]:
        """
        Select best agent for task based on capabilities and load.
        
        Args:
            required_capabilities: List of required capabilities
            
        Returns:
            Best matching agent or None
        """
        with self._lock:
            candidates = []
            
            for agent in self.agents.values():
                # Check if agent has all required capabilities
                if all(agent.can_handle(cap) for cap in required_capabilities):
                    if agent.is_available():
                        candidates.append(agent)
            
            if not candidates:
                return None
            
            # Select least loaded agent
            return min(candidates, key=lambda a: a.current_tasks)
    
    def update_status(self, agent_id: str, status: AgentStatus):
        """Update agent status"""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].status = status
    
    def claim_task(self, agent_id: str) -> bool:
        """Claim a task slot for agent"""
        with self._lock:
            agent = self.agents.get(agent_id)
            if agent and agent.is_available():
                agent.current_tasks += 1
                if agent.current_tasks >= agent.max_concurrent_tasks:
                    agent.status = AgentStatus.BUSY
                return True
            return False
    
    def release_task(self, agent_id: str):
        """Release a task slot"""
        with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent.current_tasks = max(0, agent.current_tasks - 1)
                if agent.current_tasks < agent.max_concurrent_tasks:
                    agent.status = AgentStatus.AVAILABLE
    
    def heartbeat(self, agent_id: str):
        """Update agent heartbeat"""
        with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent.last_heartbeat = datetime.utcnow()
    
    def list_all_agents(self) -> List[AgentInfo]:
        """List all registered agents"""
        with self._lock:
            return list(self.agents.values())
    
    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        with self._lock:
            return {
                "total_agents": len(self.agents),
                "available_agents": len([a for a in self.agents.values() if a.is_available()]),
                "busy_agents": len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]),
                "offline_agents": len([a for a in self.agents.values() if a.status == AgentStatus.OFFLINE]),
                "total_active_tasks": sum(a.current_tasks for a in self.agents.values())
            }


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create global agent registry"""
    global _registry
    
    if _registry is None:
        _registry = AgentRegistry()
    
    return _registry
