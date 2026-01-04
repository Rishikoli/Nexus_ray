"""
Collaboration coordinator for multi-agent workflows.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict
import threading

from src.collaboration.agent_registry import (
    AgentRegistry, AgentInfo, AgentCapability, get_agent_registry
)
from src.collaboration.message_protocol import (
    AgentMessage, MessageType, MessageProtocol
)


class ConsensusStrategy(str, Enum):
    """Consensus strategies"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    UNANIMOUS = "unanimous"
    FIRST_RESPONSE = "first_response"


@dataclass
class ConsensusResult:
    """Result of a consensus request"""
    question: str
    winning_option: Any
    votes: Dict[str, Any]  # agent_id -> vote
    vote_counts: Dict[Any, int]
    participants: int
    strategy: ConsensusStrategy
    confidence: float = 0.0


@dataclass
class SharedContext:
    """Shared context between agents"""
    context_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    contributors: set = field(default_factory=set)
    version: int = 0
    
    def update(self, key: str, value: Any, agent_id: str):
        """Update context data"""
        self.data[key] = value
        self.contributors.add(agent_id)
        self.version += 1


class CollaborationCoordinator:
    """
    Coordinates multi-agent collaboration.
    
    Features:
    - Task decomposition and delegation
    - Shared context management
    - Consensus and voting
    - Result aggregation
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or get_agent_registry()
        
        # Message handling
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.pending_responses: Dict[str, List[AgentMessage]] = defaultdict(list)
        
        # Shared contexts
        self.contexts: Dict[str, SharedContext] = {}
        
        # Consensus tracking
        self.active_consensus: Dict[str, Dict] = {}  # correlation_id -> consensus data
        
        self._lock = threading.Lock()
    
    def create_shared_context(self, context_id: str) -> SharedContext:
        """Create a new shared context"""
        with self._lock:
            context = SharedContext(context_id=context_id)
            self.contexts[context_id] = context
            return context
    
    def get_shared_context(self, context_id: str) -> Optional[SharedContext]:
        """Get shared context"""
        return self.contexts.get(context_id)
    
    def update_shared_context(
        self,
        context_id: str,
        key: str,
        value: Any,
        agent_id: str
    ):
        """Update shared context"""
        with self._lock:
            context = self.contexts.get(context_id)
            if context:
                context.update(key, value, agent_id)
    
    def delegate_task(
        self,
        task_description: str,
        required_capabilities: List[AgentCapability],
        task_data: Dict[str, Any],
        from_agent: str
    ) -> Optional[AgentInfo]:
        """
        Delegate task to best available agent.
        
        Args:
            task_description: Description of the task
            required_capabilities: Required agent capabilities
            task_data: Task input data
            from_agent: Requesting agent ID
            
        Returns:
            Selected agent or None
        """
        # Find best agent
        agent = self.registry.select_best_agent(required_capabilities)
        
        if not agent:
            return None
        
        # Claim task slot
        if not self.registry.claim_task(agent.agent_id):
            return None
        
        # Create task proposal message
        message = MessageProtocol.create_task_proposal(
            from_agent=from_agent,
            to_agent=agent.agent_id,
            task_description=task_description,
            task_data=task_data
        )
        
        # In production: send via Kafka
        # For now, just return the agent
        
        return agent
    
    def initiate_consensus(
        self,
        question: str,
        options: List[Any],
        from_agent: str,
        strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE,
        target_agents: Optional[List[str]] = None,
        timeout_seconds: int = 30
    ) -> str:
        """
        Initiate consensus request.
        
        Args:
            question: Question to vote on
            options: Available options
            from_agent: Requesting agent
            strategy: Consensus strategy
            target_agents: Specific agents to query (None = all)
            timeout_seconds: Timeout for collecting votes
            
        Returns:
            Correlation ID for tracking
        """
        message = MessageProtocol.create_consensus_request(
            from_agent=from_agent,
            question=question,
            options=options
        )
        
        correlation_id = message.correlation_id
        
        with self._lock:
            self.active_consensus[correlation_id] = {
                "message": message,
                "strategy": strategy,
                "target_agents": target_agents,
                "votes": {},
                "started_at": message.timestamp
            }
        
        # In production: broadcast via Kafka
        
        return correlation_id
    
    def submit_vote(
        self,
        correlation_id: str,
        agent_id: str,
        vote: Any,
        reasoning: Optional[str] = None
    ) -> bool:
        """
        Submit a vote for consensus.
        
        Args:
            correlation_id: Consensus correlation ID
            agent_id: Voting agent ID
            vote: Vote value
            reasoning: Optional reasoning
            
        Returns:
            True if vote accepted
        """
        with self._lock:
            consensus = self.active_consensus.get(correlation_id)
            if not consensus:
                return False
            
            consensus["votes"][agent_id] = {
                "vote": vote,
                "reasoning": reasoning
            }
            
            return True
    
    def evaluate_consensus(
        self,
        correlation_id: str
    ) -> Optional[ConsensusResult]:
        """
        Evaluate consensus and determine result.
        
        Args:
            correlation_id: Consensus correlation ID
            
        Returns:
            ConsensusResult or None if not ready
        """
        with self._lock:
            consensus = self.active_consensus.get(correlation_id)
            if not consensus:
                return None
            
            votes = consensus["votes"]
            strategy = consensus["strategy"]
            message = consensus["message"]
            
            if not votes:
                return None
            
            # Count votes
            vote_counts = defaultdict(int)
            vote_map = {}
            
            for agent_id, vote_data in votes.items():
                vote = vote_data["vote"]
                vote_counts[vote] += 1
                vote_map[agent_id] = vote
            
            # Apply strategy
            winning_option = None
            confidence = 0.0
            
            if strategy == ConsensusStrategy.MAJORITY_VOTE:
                winning_option = max(vote_counts.items(), key=lambda x: x[1])[0]
                total_votes = sum(vote_counts.values())
                confidence = vote_counts[winning_option] / total_votes
                
            elif strategy == ConsensusStrategy.UNANIMOUS:
                if len(vote_counts) == 1:
                    winning_option = list(vote_counts.keys())[0]
                    confidence = 1.0
                else:
                    # No consensus
                    winning_option = None
                    confidence = 0.0
                    
            elif strategy == ConsensusStrategy.FIRST_RESPONSE:
                # First vote wins
                first_agent = list(votes.keys())[0]
                winning_option = votes[first_agent]["vote"]
                confidence = 1.0
            
            return ConsensusResult(
                question=message.content["question"],
                winning_option=winning_option,
                votes=vote_map,
                vote_counts=dict(vote_counts),
                participants=len(votes),
                strategy=strategy,
                confidence=confidence
            )
    
    def aggregate_results(
        self,
        results: List[Dict[str, Any]],
        aggregation_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple agents.
        
        Args:
            results: List of result dictionaries
            aggregation_method: How to aggregate (merge, average, vote, etc.)
            
        Returns:
            Aggregated result
        """
        if not results:
            return {}
        
        if aggregation_method == "merge":
            # Merge all dictionaries
            aggregated = {}
            for result in results:
                aggregated.update(result)
            return aggregated
        
        elif aggregation_method == "average":
            # Average numeric values
            aggregated = {}
            for key in results[0].keys():
                values = [r.get(key) for r in results if key in r]
                if values and all(isinstance(v, (int, float)) for v in values):
                    aggregated[key] = sum(values) / len(values)
            return aggregated
        
        elif aggregation_method == "list":
            # Collect all results as list
            return {"results": results}
        
        return {}
    
    def broadcast_context(
        self,
        from_agent: str,
        context_key: str,
        context_data: Any
    ) -> AgentMessage:
        """
        Broadcast context to all agents.
        
        Args:
            from_agent: Sender agent ID
            context_key: Context identifier
            context_data: Context data
            
        Returns:
            Broadcast message
        """
        message = MessageProtocol.create_context_share(
            from_agent=from_agent,
            context_key=context_key,
            context_data=context_data
        )
        
        # In production: broadcast via Kafka
        
        return message
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collaboration statistics"""
        with self._lock:
            return {
                "active_contexts": len(self.contexts),
                "active_consensus": len(self.active_consensus),
                "pending_responses": sum(len(msgs) for msgs in self.pending_responses.values()),
                "total_context_updates": sum(c.version for c in self.contexts.values())
            }


# Global coordinator instance
_coordinator: Optional[CollaborationCoordinator] = None


def get_collaboration_coordinator() -> CollaborationCoordinator:
    """Get or create global collaboration coordinator"""
    global _coordinator
    
    if _coordinator is None:
        _coordinator = CollaborationCoordinator()
    
    return _coordinator
