"""
Collaboration API routes.
"""

from fastapi import APIRouter, HTTPException

from src.api.models import ConsensusRequest, ConsensusResponse
from src.collaboration import get_collaboration_coordinator, ConsensusStrategy

router = APIRouter()


@router.get("/agents")
async def list_collaboration_agents():
    """List agents in collaboration"""
    from src.collaboration import get_agent_registry
    
    registry = get_agent_registry()
    agents = registry.list_all_agents()
    
    return {
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "capabilities": [c.value for c in agent.capabilities],
                "status": agent.status.value
            }
            for agent in agents
        ]
    }


@router.post("/consensus", response_model=ConsensusResponse)
async def start_consensus(request: ConsensusRequest):
    """Start a consensus request"""
    coordinator = get_collaboration_coordinator()
    
    # Map string strategy to enum
    strategy_map = {
        "majority_vote": ConsensusStrategy.MAJORITY_VOTE,
        "unanimous": ConsensusStrategy.UNANIMOUS,
        "first_response": ConsensusStrategy.FIRST_RESPONSE
    }
    
    strategy = strategy_map.get(request.strategy, ConsensusStrategy.MAJORITY_VOTE)
    
    correlation_id = coordinator.initiate_consensus(
        question=request.question,
        options=request.options,
        from_agent=request.from_agent,
        strategy=strategy
    )
    
    return ConsensusResponse(
        correlation_id=correlation_id,
        question=request.question,
        winning_option=None,
        votes={},
        confidence=0.0
    )


@router.get("/consensus/{correlation_id}", response_model=ConsensusResponse)
async def get_consensus_result(correlation_id: str):
    """Get consensus result"""
    coordinator = get_collaboration_coordinator()
    
    result = coordinator.evaluate_consensus(correlation_id)
    
    if not result:
        return ConsensusResponse(
            correlation_id=correlation_id,
            question="",
            winning_option=None,
            votes={},
            confidence=0.0
        )
    
    return ConsensusResponse(
        correlation_id=correlation_id,
        question=result.question,
        winning_option=result.winning_option,
        votes=result.votes,
        confidence=result.confidence
    )
