"""
End-to-end integration tests with real workflow scenarios.

Tests complete workflows from definition to execution with all components.
"""

import pytest
import asyncio
from datetime import datetime

from src.sdk import WorkflowBuilder
from src.core.orchestrator import WorkflowOrchestrator
from src.core.task import TaskType, TaskStatus


class TestE2EWorkflows:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_simple_sequential_workflow(self):
        """Test simple 3-task sequential workflow"""
        # Build workflow
        workflow = (
            WorkflowBuilder("e2e_sequential")
            .add_task(task_id="step1", task_type=TaskType.LLM, name="Step 1")
            .add_task(task_id="step2", task_type=TaskType.TOOL, name="Step 2", depends_on=["step1"])
            .add_task(task_id="step3", task_type=TaskType.LLM, name="Step 3", depends_on=["step2"])
            .compile()
        )
        
        # Execute
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Verify execution
        assert state.status == "completed"
        assert len(state.completed_tasks) == 3
        assert "step1" in state.completed_tasks
        assert "step2" in state.completed_tasks
        assert "step3" in state.completed_tasks
    
    @pytest.mark.asyncio
    async def test_parallel_execution_workflow(self):
        """Test workflow with parallel branches"""
        workflow = (
            WorkflowBuilder("e2e_parallel")
            .add_task(task_id="init", task_type=TaskType.LLM, name="Initialize")
            .add_task(task_id="branch_a", task_type=TaskType.LLM, name="Branch A", depends_on=["init"])
            .add_task(task_id="branch_b", task_type=TaskType.TOOL, name="Branch B", depends_on=["init"])
            .add_task(task_id="merge", task_type=TaskType.LLM, name="Merge", depends_on=["branch_a", "branch_b"])
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # All tasks should be attempted
        assert state.status in ["completed", "failed"]
        assert len(state.task_results) == 4
    
    @pytest.mark.asyncio
    async def test_llm_workflow_with_prompts(self):
        """Test workflow with actual LLM tasks"""
        workflow = (
            WorkflowBuilder("e2e_llm")
            .add_llm_task(
                task_id="analyze",
                prompt="Analyze the following data: {data}",
                name="Analysis",
                inputs={"data": "sample data"}
            )
            .add_llm_task(
                task_id="summarize",
                prompt="Summarize: {analysis}",
                name="Summary",
                depends_on=["analyze"]
            )
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Should complete or fail gracefully (no real LLM)
        assert state.status in ["completed", "failed"]
        assert "analyze" in state.task_results
    
    @pytest.mark.asyncio
    async def test_hitl_workflow_gates(self):
        """Test workflow with HITL approval gates"""
        workflow = (
            WorkflowBuilder("e2e_hitl")
            .add_task(task_id="prepare", task_type=TaskType.LLM, name="Prepare")
            .add_hitl_gate(task_id="approval", after="prepare")
            .add_task(task_id="execute", task_type=TaskType.TOOL, name="Execute", depends_on=["approval"])
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Should stop at HITL gate
        assert "approval" in state.task_results
        assert state.task_results["approval"].status == TaskStatus.WAITING_HUMAN
    
    @pytest.mark.asyncio
    async def test_reference_protein_workflow(self):
        """Test pre-built protein-drug discovery workflow"""
        from src.sdk import build_protein_drug_workflow
        
        workflow = build_protein_drug_workflow()
        
        # Verify workflow structure
        assert workflow.name == "protein_drug_discovery"
        assert len(workflow.tasks) == 8  # 7 tasks + 1 HITL
        
        # Find HITL gate
        hitl_tasks = [t for t in workflow.tasks if t.task_type == TaskType.HUMAN]
        assert len(hitl_tasks) == 1
    
    @pytest.mark.asyncio
    async def test_reference_semiconductor_workflow(self):
        """Test pre-built semiconductor yield workflow"""
        from src.sdk import build_semiconductor_workflow
        
        workflow = build_semiconductor_workflow()
        
        # Verify workflow structure
        assert workflow.name == "semiconductor_yield"
        # Verify we have multiple tasks
        assert len(workflow.tasks) >= 7
        
        # Verify parallel paths exist
        defect_task = next((t for t in workflow.tasks if t.task_id == "defect_analysis"), None)
        process_task = next((t for t in workflow.tasks if t.task_id == "process_intel"), None)
        
        assert defect_task is not None
        assert process_task is not None
    
    @pytest.mark.asyncio
    async def  test_error_handling_recovery(self):
        """Test workflow error handling and retries"""
        workflow = (
            WorkflowBuilder("e2e_error")
            .add_task(task_id="task1", task_type=TaskType.LLM, name="Task 1", max_retries=2)
            .add_task(task_id="task2", task_type=TaskType.TOOL, name="Task 2", depends_on=["task1"])
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Check that workflow attempted execution
        assert len(state.task_results) >= 1


class TestE2EWithStateManagement:
    """E2E tests with state persistence"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_state_persistence(self):
        """Test workflow execution with state saving"""
        import tempfile
        import os
        from src.core.state_manager import StateManager
        
        # Create temp DB
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db_url = "sqlite:///" + path
        
        try:
            # Initialize state manager
            state_manager = StateManager(database_url=db_url)
            
            # Build and execute workflow
            workflow = (
                WorkflowBuilder("e2e_stateful")
                .add_task(task_id="task1", task_type=TaskType.LLM, name="Task 1")
               .add_task(task_id="task2", task_type=TaskType.LLM, name="Task 2", depends_on=["task1"])
                .compile()
            )
            
            # Execute
            orchestrator = WorkflowOrchestrator()
            state = await orchestrator.execute_workflow(workflow)
            
            # Manually save state (normally done by enhanced orchestrator)
            state_manager.save_workflow_state(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                status=state.status,
                workflow_definition=workflow,
                task_results={},
                completed_tasks=state.completed_tasks,
                failed_tasks=state.failed_tasks
            )
            
            # Verify state was saved
            loaded_state = state_manager.load_workflow_state(workflow.workflow_id)
            assert loaded_state is not None
            assert loaded_state["status"] == state.status
            
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestE2EPerformance:
    """Performance tests for workflows"""
    
    @pytest.mark.asyncio
    async def test_large_parallel_workflow(self):
        """Test workflow with many parallel tasks"""
        import time
        
        # Build workflow with 10 parallel tasks
        builder = WorkflowBuilder("e2e_large_parallel")
        builder.add_task(task_id="init", task_type=TaskType.LLM, name="Init")
        
        # Add 10 parallel tasks
        for i in range(10):
            builder.add_task(
                task_id=f"parallel_{i}",
                task_type=TaskType.LLM,
                name=f"Parallel {i}",
                depends_on=["init"]
            )
        
        # Add merge task
        parallel_ids = [f"parallel_{i}" for i in range(10)]
        builder.add_task(task_id="merge", task_type=TaskType.LLM, name="Merge", depends_on=parallel_ids)
        
        workflow = builder.compile()
        
        # Execute and measure time
        start = time.time()
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        duration = time.time() - start
        
        # Should complete all tasks
        assert state.status == "completed"
        assert len(state.completed_tasks) == 12  # init + 10 parallel + merge
        
        # Should be reasonably fast (parallel execution)
        assert duration < 15.0  # seconds
    
    @pytest.mark.asyncio
    async def test_deep_sequential_workflow(self):
        """Test workflow with deep task chain"""
        # Build 20-task sequential chain
        builder = WorkflowBuilder("e2e_deep")
        
        for i in range(20):
            depends = [f"task_{i-1}"] if i > 0 else []
            builder.add_task(
                task_id=f"task_{i}",
                task_type=TaskType.LLM,
                name=f"Task {i}",
                depends_on=depends
            )
        
        workflow = builder.compile()
        
        # Execute
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # All tasks should complete in order
        assert state.status == "completed"
        assert len(state.completed_tasks) == 20


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
