"""
Test core framework components - DAG, Orchestrator, SDK
"""

import pytest
import asyncio
from src.core import WorkflowDAG, TaskDefinition, TaskType, WorkflowOrchestrator
from src.sdk import WorkflowBuilder


class TestWorkflowDAG:
    """Test DAG construction and validation"""
    
    def test_create_empty_dag(self):
        """Create empty DAG"""
        dag = WorkflowDAG("test-workflow")
        assert dag.workflow_id == "test-workflow"
        assert dag.task_count == 0
    
    def test_add_single_task(self):
        """Add single task to DAG"""
        dag = WorkflowDAG("test-workflow")
        
        task = TaskDefinition(
            task_id="task1",
            name="Test Task",
            task_type=TaskType.LLM
        )
        
        dag.add_task(task)
        
        assert dag.task_count == 1
        assert dag.get_task("task1") == task
    
    def test_add_dependency(self):
        """Add dependency between tasks"""
        dag = WorkflowDAG("test-workflow")
        
        task1 = TaskDefinition(task_id="task1", name="Task 1", task_type=TaskType.LLM)
        task2 = TaskDefinition(task_id="task2", name="Task 2", task_type=TaskType.TOOL)
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_dependency("task1", "task2")
        
        deps = dag.get_task_dependencies("task2")
        assert "task1" in deps
    
    def test_detect_cycle(self):
        """Detect cyclic dependencies"""
        dag = WorkflowDAG("test-workflow")
        
        task1 = TaskDefinition(task_id="task1", name="Task 1", task_type=TaskType.LLM)
        task2 = TaskDefinition(task_id="task2", name="Task 2", task_type=TaskType.TOOL)
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_dependency("task1", "task2")
        
        # This should raise CyclicDependencyError
        with pytest.raises(Exception):
            dag.add_dependency("task2", "task1")
    
    def test_execution_order(self):
        """Get topological execution order"""
        dag = WorkflowDAG("test-workflow")
        
        # Create linear workflow: task1 -> task2 -> task3
        for i in range(1, 4):
            task = TaskDefinition(
                task_id=f"task{i}",
                name=f"Task {i}",
                task_type=TaskType.LLM
            )
            dag.add_task(task)
        
        dag.add_dependency("task1", "task2")
        dag.add_dependency("task2", "task3")
        
        order = dag.get_execution_order()
        
        # Should be 3 batches (sequential)
        assert len(order) == 3
        assert order[0] == ["task1"]
        assert order[1] == ["task2"]
        assert order[2] == ["task3"]


class TestWorkflowBuilder:
    """Test SDK WorkflowBuilder"""
    
    def test_create_workflow(self):
        """Create workflow using builder"""
        workflow = WorkflowBuilder("test_workflow")
        
        workflow.add_task(
            task_id="task1",
            task_type=TaskType.LLM,
            name="LLM Task"
        )
        
        definition = workflow.compile()
        
        assert definition.name == "test_workflow"
        assert len(definition.tasks) == 1
    
    def test_add_llm_task(self):
        """Add LLM task using convenience method"""
        workflow = WorkflowBuilder("test")
        
        workflow.add_llm_task(
            task_id="llm1",
            prompt="Test prompt",
            model="mistral-7b-ov"
        )
        
        definition = workflow.compile()
        task = definition.tasks[0]
        
        assert task.task_type == TaskType.LLM
        assert task.executor_config["prompt"] == "Test prompt"
    
    def test_add_hitl_gate(self):
        """Add HITL gate"""
        workflow = WorkflowBuilder("test")
        
        workflow.add_task(
            task_id="task1",
            task_type=TaskType.LLM,
            name="Task 1"
        )
        
        workflow.add_hitl_gate(
            task_id="approval",
            after="task1",
            approvers=["user@example.com"]
        )
        
        definition = workflow.compile()
        
        assert len(definition.tasks) == 2
        assert definition.tasks[1].task_type == TaskType.HUMAN


@pytest.mark.asyncio
class TestWorkflowOrchestrator:
    """Test workflow execution"""
    
    async def test_execute_simple_workflow(self):
        """Execute simple 2-task workflow"""
        workflow = WorkflowBuilder("simple_test")
        
        workflow.add_task(
            task_id="task1",
            task_type=TaskType.LLM,
            name="First Task"
        )
        
        workflow.add_task(
            task_id="task2",
            task_type=TaskType.TOOL,
            name="Second Task",
            depends_on=["task1"]
        )
        
        workflow_def = workflow.compile()
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow_def)
        
        # Check workflow completed
        assert state.status == "completed"
        assert len(state.completed_tasks) == 2
    
    async def test_parallel_execution(self):
        """Execute tasks in parallel"""
        workflow = WorkflowBuilder("parallel_test")
        
        # Root task
        workflow.add_task(
            task_id="root",
            task_type=TaskType.LLM,
            name="Root"
        )
        
        # Two parallel tasks
        workflow.add_task(
            task_id="parallel1",
            task_type=TaskType.TOOL,
            name="Parallel 1",
            depends_on=["root"]
        )
        
        workflow.add_task(
            task_id="parallel2",
            task_type=TaskType.TOOL,
            name="Parallel 2",
            depends_on=["root"]
        )
        
        workflow_def = workflow.compile()
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow_def)
        
        assert state.status == "completed"
        assert len(state.completed_tasks) == 3


def test_protein_drug_workflow_definition():
    """Test protein-drug workflow builds correctly"""
    from src.sdk import build_protein_drug_workflow
    
    workflow_def = build_protein_drug_workflow()
    
    assert workflow_def.name == "protein_drug_discovery"
    assert len(workflow_def.tasks) == 8  # 7 agents/tasks + 1 HITL


def test_semiconductor_workflow_definition():
    """Test semiconductor workflow builds correctly"""
    from src.sdk import build_semiconductor_workflow
    
    workflow_def = build_semiconductor_workflow()
    
    assert workflow_def.name == "semiconductor_yield"
    # Check has parallel paths
    task_ids = [t.task_id for t in workflow_def.tasks]
    assert "defect_analysis" in task_ids
    assert "process_intel" in task_ids
