"""
Human-in-the-Loop (HITL) API routes.

Manages approval requests requiring human intervention.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import time
from enum import Enum

router = APIRouter()

class HITLAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"

class HITLRequest(BaseModel):
    workflow_id: str
    task_id: str
    description: str
    severity: str = "medium" # low, medium, high, critical
    context: Dict[str, Any] = {}
    options: List[str] = ["approve", "reject"]
    
class HITLDecision(BaseModel):
    action: HITLAction
    comment: Optional[str] = None
    modified_data: Optional[Dict[str, Any]] = None

class HITLResponse(BaseModel):
    request_id: str
    status: str
    created_at: float
    workflow_id: str
    description: str
    severity: str
    context: Dict[str, Any]
    
# In-memory storage for HITL requests (replace with DB in production)
hitl_store: Dict[str, Dict] = {}

@router.post("/request", response_model=HITLResponse)
async def create_hitl_request(request: HITLRequest):
    """
    Internal endpoint: Agents call this to pause and request human approval.
    """
    request_id = str(uuid.uuid4())
    
    hitl_store[request_id] = {
        "request_id": request_id,
        "workflow_id": request.workflow_id,
        "task_id": request.task_id,
        "description": request.description,
        "severity": request.severity,
        "context": request.context,
        "status": "pending",
        "created_at": time.time(),
        "decision": None
    }
    
    return hitl_store[request_id]

@router.get("/pending", response_model=List[HITLResponse])
async def get_pending_requests():
    """
    Frontend endpoint: Get all pending approval requests.
    """
    return [
        req for req in hitl_store.values() 
        if req["status"] == "pending"
    ]

@router.post("/{request_id}/decision")
async def submit_decision(request_id: str, decision: HITLDecision):
    """
    Frontend endpoint: Submit human decision (Approve/Reject).
    """
    if request_id not in hitl_store:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req = hitl_store[request_id]
    
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
        
    # Update status
    req["status"] = "resolved"
    req["decision"] = decision.dict()
    req["resolved_at"] = time.time()
    
    return {"message": "Decision recorded", "decision": req["decision"]}

@router.get("/{request_id}/status")
async def check_request_status(request_id: str):
    """
    Agent endpoint: Poll this to see if human has decided.
    """
    if request_id not in hitl_store:
        raise HTTPException(status_code=404, detail="Request not found")
        
    return hitl_store[request_id]
