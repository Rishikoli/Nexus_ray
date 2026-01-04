"""
Workflow API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from src.api.models import (
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowExecutionResponse
)
from src.sdk import WorkflowBuilder
from src.core import WorkflowOrchestrator

router = APIRouter()

# In-memory storage (replace with database in production)
workflows_db = {}
executions_db = {}


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new workflow"""
    workflow_id = str(uuid.uuid4())
    
    workflow_data = {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "status": "created",
        "created_at": datetime.utcnow(),
        "tasks": request.tasks
    }
    
    workflows_db[workflow_id] = workflow_data
    
    return WorkflowResponse(**workflow_data)


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows():
    """List all workflows"""
    return [WorkflowResponse(**wf) for wf in workflows_db.values()]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a workflow by ID"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowResponse(**workflows_db[workflow_id])


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """Execute a workflow"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    execution_id = str(uuid.uuid4())
    
    execution_data = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "result": None
    }
    
    executions_db[execution_id] = execution_data
    
    # In production: execute workflow asynchronously
    # For now, return execution ID
    
    return WorkflowExecutionResponse(**execution_data)


@router.get("/{workflow_id}/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution_status(workflow_id: str, execution_id: str):
    """Get execution status"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return WorkflowExecutionResponse(**executions_db[execution_id])


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows_db[workflow_id]
    
    return {"message": "Workflow deleted"}
