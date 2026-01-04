"""
Unit tests for state persistence components.

Tests state manager database operations and recovery.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os

from src.core.state_manager import StateManager, WorkflowStateDB, TaskExecutionDB
from src.core.task import TaskStatus, WorkflowDefinition, TaskDefinition, TaskType


class TestStateManager:
    """Test state manager persistence"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db_url = "sqlite:///" + path
        yield db_url
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def state_manager(self, temp_db):
        """Create state manager with temp DB"""
        return StateManager(database_url=temp_db)
    
    def test_state_manager_initialization(self, state_manager):
        """Test state manager initialization"""
        assert state_manager is not None
        assert state_manager.database_url is not None
    
    def test_save_workflow_state(self, state_manager):
        """Test saving workflow state"""
        workflow_def = WorkflowDefinition(
            workflow_id="wf-123",
            name="test_workflow",
            tasks=[]
        )
        
        state_manager.save_workflow_state(
            workflow_id="wf-123",
            name="test_workflow",
            status="running",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=[]
        )
        
        # Verify saved
        state = state_manager.load_workflow_state("wf-123")
        assert state is not None
        assert state["workflow_id"] == "wf-123"
    
    def test_update_workflow_status(self, state_manager):
        """Test updating workflow status"""
        workflow_def = WorkflowDefinition(
            workflow_id="wf-123",
            name="test_workflow",
            tasks=[]
        )
        
        # Save initial
        state_manager.save_workflow_state(
            workflow_id="wf-123",
            name="test_workflow",
            status="running",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=[]
        )
        
        # Update status
        state_manager.save_workflow_state(
            workflow_id="wf-123",
            name="test_workflow",
            status="completed",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=[]
        )
        
        state = state_manager.load_workflow_state("wf-123")
        assert state["status"] == "completed"
    
    def test_save_task_execution(self, state_manager):
        """Test saving task execution"""
        state_manager.save_task_execution(
            workflow_id="wf-123",
            task_id="task-1",
            status=TaskStatus.SUCCESS,
            inputs={"test": "data"},
            outputs={"result": "success"},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=1000,
            retry_count=0
        )
        
        # Verify saved
        executions = state_manager.get_task_executions("wf-123")
        assert len(executions) == 1
        assert executions[0]["status"] == TaskStatus.SUCCESS.value
    
    def test_list_workflows(self, state_manager):
        """Test listing workflows"""
        # Save multiple workflows
        for i in range(3):
            workflow_def = WorkflowDefinition(
                workflow_id=f"wf-{i}",
                name=f"workflow_{i}",
                tasks=[]
            )
            
            state_manager.save_workflow_state(
                workflow_id=f"wf-{i}",
                name=f"workflow_{i}",
                status="completed",
                workflow_definition=workflow_def,
                task_results={},
                completed_tasks=[],
                failed_tasks=[]
            )
        
        workflows = state_manager.list_workflows(limit=10)
        assert len(workflows) >= 3
    
    def test_list_failed_workflows(self, state_manager):
        """Test getting failed workflows"""
        # Save failed workflow
        workflow_def = WorkflowDefinition(
            workflow_id="wf-fail",
            name="failed_workflow",
            tasks=[]
        )
        
        state_manager.save_workflow_state(
            workflow_id="wf-fail",
            name="failed_workflow",
            status="failed",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=["task-1"]
        )
        
        failed = state_manager.list_workflows(status="failed")
        assert len(failed) >= 1
        assert any(w["workflow_id"] == "wf-fail" for w in failed)
    
    def test_recovery_from_database(self, temp_db):
        """Test recovering state from database"""
        # First instance
        manager1 = StateManager(database_url=temp_db)
        
        workflow_def = WorkflowDefinition(
            workflow_id="wf-recovery",
            name="recovery_test",
            tasks=[]
        )
        
        manager1.save_workflow_state(
            workflow_id="wf-recovery",
            name="recovery_test",
            status="running",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=[]
        )
        
        # New instance (simulating restart)
        manager2 = StateManager(database_url=temp_db)
        state = manager2.load_workflow_state("wf-recovery")
        
        assert state is not None
        assert state["workflow_id"] == "wf-recovery"


class TestStatePersistenceIntegration:
    """Integration tests for state persistence"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db_url = "sqlite:///" + path
        yield db_url
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.mark.asyncio
    async def test_workflow_state_lifecycle(self, temp_db):
        """Test complete workflow state lifecycle"""
        manager = StateManager(database_url=temp_db)
        
        # Create workflow
        task1 = TaskDefinition(
            task_id="task1",
            name="Task 1",
            task_type=TaskType.LLM
        )
        
        workflow_def = WorkflowDefinition(
            workflow_id="wf-lifecycle",
            name="lifecycle_test",
            tasks=[task1]
        )
        
        # 1. Save initial state (running)
        manager.save_workflow_state(
            workflow_id="wf-lifecycle",
            name="lifecycle_test",
            status="running",
            workflow_definition=workflow_def,
            task_results={},
            completed_tasks=[],
            failed_tasks=[],
            started_at=datetime.utcnow()
        )
        
        # 2. Save task execution
        manager.save_task_execution(
            workflow_id="wf-lifecycle",
            task_id="task1",
            status=TaskStatus.SUCCESS,
            inputs={},
            outputs={"result": "success"},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=500
        )
        
        # 3. Update workflow status (completed)
        manager.save_workflow_state(
            workflow_id="wf-lifecycle",
            name="lifecycle_test",
            status="completed",
            workflow_definition=workflow_def,
            task_results={"task1": {"status": "success"}},
            completed_tasks=["task1"],
            failed_tasks=[],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # Verify final state
        state = manager.load_workflow_state("wf-lifecycle")
        assert state["status"] == "completed"
        
        executions = manager.get_task_executions("wf-lifecycle")
        assert len(executions) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
