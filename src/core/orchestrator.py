"""
Workflow orchestrator - manages workflow lifecycle and execution.
"""

import asyncio
from typing import Dict, Set, Optional, List
from datetime import datetime
from loguru import logger

from src.core.dag import WorkflowDAG
from src.core.task import (
    TaskDefinition,
    TaskResult,
    TaskStatus,
    TaskType,
    WorkflowDefinition
)
from src.core.executor import (
    BaseExecutor,
    LLMExecutor,
    ToolExecutor,
    HumanExecutor,
    AgentExecutor
)


class WorkflowState:
    """Tracks the current state of a workflow execution"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.status = "running"
        self.task_results: Dict[str, TaskResult] = {}
        self.completed_tasks: Set[str] = set()
        self.running_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if workflow is in terminal state"""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage"""
        total = len(self.task_results)
        if total == 0:
            return 0.0
        return (len(self.completed_tasks) / total) * 100


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution using DAG-based task scheduling.
    
    Key responsibilities:
    - Execute tasks in topological order
    - Handle parallel execution of independent tasks
    - Manage task retries and timeouts
    - Coordinate with executors
    - Track workflow state
    """
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowState] = {}
        self.dags: Dict[str, WorkflowDAG] = {}
        
        # Initialize executors
        self.executors: Dict[TaskType, BaseExecutor] = {
            TaskType.LLM: LLMExecutor(),
            TaskType.TOOL: ToolExecutor(),
            TaskType.HUMAN: HumanExecutor(),
        }
        
        logger.info("WorkflowOrchestrator initialized")
    
    async def execute_workflow(
        self,
        workflow_def: WorkflowDefinition,
        inputs: Optional[Dict] = None
    ) -> WorkflowState:
        """
        Execute a complete workflow.
        
        Args:
            workflow_def: Workflow definition with tasks
            inputs: Initial workflow inputs
            
        Returns:
            WorkflowState with final results
        """
        workflow_id = workflow_def.workflow_id
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        # Build DAG
        dag = self._build_dag(workflow_def)
        self.dags[workflow_id] = dag
        
        # Validate DAG
        dag.validate()
        
        # Initialize state
        state = WorkflowState(workflow_id)
        self.workflows[workflow_id] = state
        
        # Initialize task results
        for task in workflow_def.tasks:
            state.task_results[task.task_id] = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.PENDING
            )
        
        try:
            # Execute tasks in topological order with parallelism
            await self._execute_dag(dag, state, inputs or {})
            
            # Mark workflow as complete
            state.status = "completed" if not state.failed_tasks else "failed"
            state.completed_at = datetime.utcnow()
            
            duration = (state.completed_at - state.started_at).total_seconds()
            logger.info(
                f"Workflow {workflow_id} {state.status} in {duration:.2f}s "
                f"({len(state.completed_tasks)}/{len(workflow_def.tasks)} tasks)"
            )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            state.status = "failed"
            state.completed_at = datetime.utcnow()
            raise
        
        return state
    
    async def _execute_dag(
        self,
        dag: WorkflowDAG,
        state: WorkflowState,
        workflow_inputs: Dict
    ) -> None:
        """
        Execute DAG tasks with parallel batch execution.
        
        Processes tasks in topological order, running independent tasks in parallel.
        """
        execution_order = dag.get_execution_order()
        
        logger.info(f"Executing {len(execution_order)} batches")
        
        for batch_idx, batch in enumerate(execution_order):
            logger.debug(f"Batch {batch_idx}: {batch}")
            
            # Execute all tasks in batch concurrently
            tasks_to_run = []
            for task_id in batch:
                task = dag.get_task(task_id)
                tasks_to_run.append(self._execute_task(task, state, workflow_inputs))
            
            # Wait for all tasks in batch to complete
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            # Check for failures
            for task_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task_id} raised exception: {result}")
                    state.failed_tasks.add(task_id)
                    # Optionally: fail fast or continue
                    # For now, we'll continue to see all failures
    
    async def _execute_task(
        self,
        task: TaskDefinition,
        state: WorkflowState,
        workflow_inputs: Dict
    ) -> TaskResult:
        """
        Execute a single task with retry logic.
        
        Args:
            task: Task to execute
            state: Current workflow state
            workflow_inputs: Workflow-level inputs
            
        Returns:
            TaskResult
        """
        task_id = task.task_id
        retry_count = 0
        max_retries = task.max_retries
        
        logger.info(f"Executing task {task_id} ({task.name})")
        state.running_tasks.add(task_id)
        
        while retry_count <= max_retries:
            try:
                # Prepare task inputs (merge workflow inputs + task inputs)
                task_inputs = {**workflow_inputs, **task.inputs}
                
                # Resolve dependencies (get outputs from completed tasks)
                task_inputs = self._resolve_task_inputs(
                    task, state, task_inputs
                )
                
                # Update task with resolved inputs
                task.inputs = task_inputs
                
                # Get appropriate executor
                executor = self._get_executor(task)
                
                # Execute with timeout if specified
                if task.timeout_seconds:
                    result = await asyncio.wait_for(
                        executor.run_with_metrics(task),
                        timeout=task.timeout_seconds
                    )
                else:
                    result = await executor.run_with_metrics(task)
                
                # Update retry count in result
                result.retry_count = retry_count
                
                # Save result
                state.task_results[task_id] = result
                
                # Update state based on result
                if result.status == TaskStatus.SUCCESS:
                    state.completed_tasks.add(task_id)
                    state.running_tasks.discard(task_id)
                    logger.info(f"Task {task_id} succeeded")
                    return result
                    
                elif result.status == TaskStatus.WAITING_HUMAN:
                    # HITL - pause here
                    logger.info(f"Task {task_id} waiting for human approval")
                    # In real implementation, this would wait for API call
                    # For now, we'll mark as completed
                    state.completed_tasks.add(task_id)
                    state.running_tasks.discard(task_id)
                    return result
                    
                elif result.status == TaskStatus.FAILED:
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.warning(
                            f"Task {task_id} failed, retrying "
                            f"({retry_count}/{max_retries})"
                        )
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Task {task_id} failed after {max_retries} retries")
                        state.failed_tasks.add(task_id)
                        state.running_tasks.discard(task_id)
                        return result
                
            except asyncio.TimeoutError:
                logger.error(f"Task {task_id} timed out after {task.timeout_seconds}s")
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=f"Timeout after {task.timeout_seconds}s",
                    retry_count=retry_count
                )
                state.task_results[task_id] = result
                state.failed_tasks.add(task_id)
                state.running_tasks.discard(task_id)
                return result
                
            except Exception as e:
                logger.error(f"Task {task_id} raised exception: {e}", exc_info=True)
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    retry_count=retry_count
                )
                state.task_results[task_id] = result
                state.failed_tasks.add(task_id)
                state.running_tasks.discard(task_id)
                return result
        
        # Should not reach here
        raise RuntimeError(f"Task {task_id} execution logic error")
    
    def _resolve_task_inputs(
        self,
        task: TaskDefinition,
        state: WorkflowState,
        base_inputs: Dict
    ) -> Dict:
        """
        Resolve task inputs from dependency outputs.
        
        Supports template syntax like: {{previous_task.output.field}}
        """
        resolved = {**base_inputs}
        
        # Get outputs from dependencies
        for dep_task_id in task.depends_on:
            if dep_task_id in state.task_results:
                dep_result = state.task_results[dep_task_id]
                if dep_result.status == TaskStatus.SUCCESS:
                    # Make dependency outputs available
                   resolved[f"{dep_task_id}_output"] = dep_result.outputs
        
        return resolved
    
    def _get_executor(self, task: TaskDefinition) -> BaseExecutor:
        """Get appropriate executor for task type"""
        if task.task_type == TaskType.AGENT:
            # Would need agent instance from task config
            raise NotImplementedError("Agent executor requires agent instance")
        
        return self.executors[task.task_type]
    
    def _build_dag(self, workflow_def: WorkflowDefinition) -> WorkflowDAG:
        """Build DAG from workflow definition"""
        dag = WorkflowDAG(workflow_def.workflow_id)
        
        # Add all tasks
        for task in workflow_def.tasks:
            dag.add_task(task)
        
        # Add dependencies
        for task in workflow_def.tasks:
            for dep in task.depends_on:
                dag.add_dependency(dep, task.task_id)
        
        return dag
    
    async def pause_workflow(self, workflow_id: str) -> None:
        """Pause a running workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = "paused"
            logger.info(f"Workflow {workflow_id} paused")
    
    async def resume_workflow(self, workflow_id: str) -> None:
        """Resume a paused workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = "running"
            logger.info(f"Workflow {workflow_id} resumed")
    
    async def cancel_workflow(self, workflow_id: str) -> None:
        """Cancel a running workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = "cancelled"
            logger.info(f"Workflow {workflow_id} cancelled")
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get current state of a workflow"""
        return self.workflows.get(workflow_id)
