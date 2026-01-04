"""
Agent API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from src.api.models import AgentRegisterRequest, AgentResponse
from src.collaboration import get_agent_registry, AgentCapability

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all registered agents"""
    registry = get_agent_registry()
    agents = registry.list_all_agents()
    
    return [
        AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            capabilities=[c.value for c in agent.capabilities],
            status=agent.status.value,
            current_tasks=agent.current_tasks,
            max_concurrent_tasks=agent.max_concurrent_tasks
        )
        for agent in agents
    ]


@router.post("/register", response_model=AgentResponse, status_code=201)
async def register_agent(request: AgentRegisterRequest):
    """Register a new agent"""
    registry = get_agent_registry()
    
    # Convert string capabilities to enum
    capabilities = [AgentCapability(cap) for cap in request.capabilities]
    
    agent_info = registry.register(
        agent_id=request.agent_id,
        name=request.name,
        capabilities=capabilities,
        metadata=request.metadata
    )
    
    return AgentResponse(
        agent_id=agent_info.agent_id,
        name=agent_info.name,
        capabilities=[c.value for c in agent_info.capabilities],
        status=agent_info.status.value,
        current_tasks=agent_info.current_tasks,
        max_concurrent_tasks=agent_info.max_concurrent_tasks
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent details"""
    registry = get_agent_registry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        capabilities=[c.value for c in agent.capabilities],
        status=agent.status.value,
        current_tasks=agent.current_tasks,
        max_concurrent_tasks=agent.max_concurrent_tasks
    )


@router.delete("/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent"""
    registry = get_agent_registry()
    
    if not registry.unregister(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent unregistered"}
