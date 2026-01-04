"""
Enhanced orchestrator with Kafka events and state persistence integration.
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
from src.core.state_manager import StateManager
from src.core.config import get_settings
from src.messaging import KafkaClient, MessageRouter, MessageType
from src.observability import get_notion_sync


class WorkflowState:
    """Tracks the current state of a workflow execution"""
    
    def __init__(self, workflow_id: str, workflow_name: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
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


class EnhancedOrchestrator:
    """
    Enhanced orchestrator with Kafka events and state persistence.
    
    Improvements over base orchestrator:
    - Publishes workflow events to Kafka
    - Persists state to database for recovery
    - Better error handling and logging
    - Configurable via settings
    """
    
    def __init__(
        self,
        kafka_client: Optional[KafkaClient] = None,
        state_manager: Optional[StateManager] = None
    ):
        self.settings = get_settings()
        self.workflows: Dict[str, WorkflowState] = {}
        self.dags: Dict[str, WorkflowDAG] = {}
        
        # Initialize executors
        self.executors: Dict[TaskType, BaseExecutor] = {
            TaskType.LLM: LLMExecutor(),
            TaskType.TOOL: ToolExecutor(),
            TaskType.HUMAN: HumanExecutor(),
        }
        
        # Kafka integration
        self.kafka_client = kafka_client
        self.message_router = MessageRouter()
        self._kafka_enabled = kafka_client is not None
        
        # State persistence
        self.state_manager = state_manager
        self._persistence_enabled = (
            state_manager is not None and
            self.settings.workflow.state_persistence_enabled
        )
        
        # Notion sync
        self.notion_sync = get_notion_sync()
        self._notion_enabled = self.notion_sync.is_enabled()
        
        logger.info(
            f"EnhancedOrchestrator initialized "
            f"(Kafka: {self._kafka_enabled}, Persistence: {self._persistence_enabled}, Notion: {self._notion_enabled})"
        )
    
    async def _publish_event(self, message: Dict) -> None:
        """Publish event to Kafka if enabled"""
        if not self._kafka_enabled or not self.kafka_client:
            return
        
        try:
            topic = self.message_router.route_message(message)
            await self.kafka_client.publish(topic, message)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            # Don't fail workflow due to event publishing error
    
    async def _persist_state(
        self,
        workflow_id: str,
        workflow_def: WorkflowDefinition,
        state: WorkflowState
    ) -> None:
        """Persist workflow state if enabled"""
        if not self._persistence_enabled or not self.state_manager:
            return
        
        try:
            self.state_manager.save_workflow_state(
                workflow_id=workflow_id,
                name=state.workflow_name,
                status=state.status,
                workflow_definition=workflow_def,
                task_results={k: v.dict() for k, v in state.task_results.items()},
                completed_tasks=list(state.completed_tasks),
                failed_tasks=list(state.failed_tasks),
                started_at=state.started_at,
                completed_at=state.completed_at
            )
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")
            # Don't fail workflow due to persistence error
    
    async def execute_workflow(
        self,
        workflow_def: WorkflowDefinition,
        inputs: Optional[Dict] = None
    ) -> WorkflowState:
        """
        Execute a complete workflow with integrated events and persistence.
        
        Args:
            workflow_def: Workflow definition with tasks
            inputs: Initial workflow inputs
            
        Returns:
            WorkflowState with final results
        """
        workflow_id = workflow_def.workflow_id
        logger.info(f"Starting workflow execution: {workflow_id} ({workflow_def.name})")
        
        # Build DAG
        dag = self._build_dag(workflow_def)
        self.dags[workflow_id] = dag
        
        # Validate DAG
        dag.validate()
        
        # Initialize state
        state = WorkflowState(workflow_id, workflow_def.name)
        self.workflows[workflow_id] = state
        
        # Initialize task results
        for task in workflow_def.tasks:
            state.task_results[task.task_id] = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.PENDING
            )
        
        # Publish workflow started event
        await self._publish_event(
            self.message_router.create_workflow_event(
                MessageType.WORKFLOW_STARTED,
                workflow_id,
                workflow_name=workflow_def.name,
                total_tasks=len(workflow_def.tasks)
            )
        )
        
        # Persist initial state
        await self._persist_state(workflow_id, workflow_def, state)
        
        # Sync to Notion (workflow definition)
        notion_workflow_page_id = None
        if self._notion_enabled and self.settings.notion.auto_sync:
            notion_workflow_page_id = await self.notion_sync.sync_workflow_definition(workflow_def)
        
        # Sync to Notion (execution log)
        notion_execution_page_id = None
        if self._notion_enabled and self.settings.notion.auto_sync:
            notion_execution_page_id = await self.notion_sync.sync_execution_start(
                workflow_id,
                workflow_def.name,
                state.started_at
            )
        
        try:
            # Execute tasks in topological order with parallelism
            await self._execute_dag(dag, state, workflow_def, inputs or {})
            
            # Mark workflow as complete
            state.status = "completed" if not state.failed_tasks else "failed"
            state.completed_at = datetime.utcnow()
            
            duration = (state.completed_at - state.started_at).total_seconds()
            logger.info(
                f"Workflow {workflow_id} {state.status} in {duration:.2f}s "
                f"({len(state.completed_tasks)}/{len(workflow_def.tasks)} tasks)"
            )
            
            # Publish completion event
            event_type = (
                MessageType.WORKFLOW_COMPLETED 
                if state.status == "completed" 
                else MessageType.WORKFLOW_FAILED
            )
            await self._publish_event(
                self.message_router.create_workflow_event(
                    event_type,
                    workflow_id,
                    duration_seconds=duration,
                    completed_tasks=len(state.completed_tasks),
                    failed_tasks=len(state.failed_tasks)
                )
            )
            
            # Persist final state
            await self._persist_state(workflow_id, workflow_def, state)
            
            # Sync to Notion (completion)
            if self._notion_enabled and notion_execution_page_id:
                await self.notion_sync.sync_execution_complete(
                    notion_execution_page_id,
                    workflow_id,
                    state.status,
                    state.completed_at,
                    state.task_results
                )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            state.status = "failed"
            state.completed_at = datetime.utcnow()
            
            # Publish failure event
            await self._publish_event(
                self.message_router.create_workflow_event(
                    MessageType.WORKFLOW_FAILED,
                    workflow_id,
                    error=str(e)
                )
            )
            
            # Persist error state
            await self._persist_state(workflow_id, workflow_def, state)
            
            raise
        
        return state
    
    async def _execute_dag(
        self,
        dag: WorkflowDAG,
        state: WorkflowState,
        workflow_def: WorkflowDefinition,
        workflow_inputs: Dict
    ) -> None:
        """Execute DAG tasks with parallel batch execution and events"""
        execution_order = dag.get_execution_order()
        
        logger.info(f"Executing {len(execution_order)} batches")
        
        for batch_idx, batch in enumerate(execution_order):
            logger.debug(f"Batch {batch_idx}: {batch}")
            
            # Execute all tasks in batch concurrently
            tasks_to_run = []
            for task_id in batch:
                task = dag.get_task(task_id)
                tasks_to_run.append(
                    self._execute_task(task, state, workflow_def, workflow_inputs)
                )
            
            # Wait for all tasks in batch to complete
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            # Check for failures
            for task_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task_id} raised exception: {result}")
                    state.failed_tasks.add(task_id)
            
            # Persist state after each batch
            await self._persist_state(state.workflow_id, workflow_def, state)
    
    async def _execute_task(
        self,
        task: TaskDefinition,
        state: WorkflowState,
        workflow_def: WorkflowDefinition,
        workflow_inputs: Dict
    ) -> TaskResult:
        """Execute a single task with retry logic and events"""
        task_id = task.task_id
        retry_count = 0
        max_retries = task.max_retries
        
        logger.info(f"Executing task {task_id} ({task.name})")
        state.running_tasks.add(task_id)
        
        # Publish task started event
        await self._publish_event(
            self.message_router.create_workflow_event(
                MessageType.TASK_STARTED,
                state.workflow_id,
                task_id=task_id,
                task_name=task.name
            )
        )
        
        while retry_count <= max_retries:
            try:
                # Prepare task inputs
                task_inputs = {**workflow_inputs, **task.inputs}
                task_inputs = self._resolve_task_inputs(task, state, task_inputs)
                task.inputs = task_inputs
                
                # Get executor
                executor = self._get_executor(task)
                
                # Execute with timeout
                if task.timeout_seconds:
                    result = await asyncio.wait_for(
                        executor.run_with_metrics(task),
                        timeout=task.timeout_seconds
                    )
                else:
                    result = await executor.run_with_metrics(task)
                
                result.retry_count = retry_count
                state.task_results[task_id] = result
                
                # Handle result
                if result.status == TaskStatus.SUCCESS:
                    state.completed_tasks.add(task_id)
                    state.running_tasks.discard(task_id)
                    logger.info(f"Task {task_id} succeeded")
                    
                    # Publish success event
                    await self._publish_event(
                        self.message_router.create_workflow_event(
                            MessageType.TASK_COMPLETED,
                            state.workflow_id,
                            task_id=task_id,
                            duration_ms=result.duration_ms
                        )
                    )
                    
                    # Persist task execution
                    if self._persistence_enabled and self.state_manager:
                        self.state_manager.save_task_execution(
                            workflow_id=state.workflow_id,
                            task_id=task_id,
                            status=result.status,
                            inputs=task.inputs,
                            outputs=result.outputs,
                            started_at=result.started_at,
                            completed_at=result.completed_at,
                            duration_ms=result.duration_ms,
                            retry_count=retry_count,
                            metrics=result.metrics
                        )
                    
                    return result
                    
                elif result.status == TaskStatus.WAITING_HUMAN:
                    logger.info(f"Task {task_id} waiting for human approval")
                    state.completed_tasks.add(task_id)
                    state.running_tasks.discard(task_id)
                    
                    # Publish HITL event
                    await self._publish_event(
                        self.message_router.create_hitl_request(
                            workflow_id=state.workflow_id,
                            task_id=task_id,
                            decision_data=result.outputs,
                            approvers=task.hitl_config.get('approvers', []) if task.hitl_config else []
                        )
                    )
                    
                    return result
                    
                elif result.status == TaskStatus.FAILED:
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.warning(f"Task {task_id} failed, retrying ({retry_count}/{max_retries})")
                        await asyncio.sleep(self.settings.workflow.retry_backoff_base ** retry_count)
                        continue
                    else:
                        logger.error(f"Task {task_id} failed after {max_retries} retries")
                        state.failed_tasks.add(task_id)
                        state.running_tasks.discard(task_id)
                        
                        # Publish failure event
                        await self._publish_event(
                            self.message_router.create_workflow_event(
                                MessageType.TASK_FAILED,
                                state.workflow_id,
                                task_id=task_id,
                                error=result.error
                            )
                        )
                        
                        return result
                
            except asyncio.TimeoutError:
                logger.error(f"Task {task_id} timed out")
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=f"Timeout after {task.timeout_seconds}s",
                    retry_count=retry_count
                )
                state.task_results[task_id] = result
                state.failed_tasks.add(task_id)
                state.running_tasks.discard(task_id)
                
                await self._publish_event(
                    self.message_router.create_workflow_event(
                        MessageType.TASK_FAILED,
                        state.workflow_id,
                        task_id=task_id,
                        error=result.error
                    )
                )
                
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
                
                await self._publish_event(
                    self.message_router.create_workflow_event(
                        MessageType.TASK_FAILED,
                        state.workflow_id,
                        task_id=task_id,
                        error=str(e)
                    )
                )
                
                return result
        
        raise RuntimeError(f"Task {task_id} execution logic error")
    
    def _resolve_task_inputs(
        self,
        task: TaskDefinition,
        state: WorkflowState,
        base_inputs: Dict
    ) -> Dict:
        """Resolve task inputs from dependency outputs"""
        resolved = {**base_inputs}
        
        for dep_task_id in task.depends_on:
            if dep_task_id in state.task_results:
                dep_result = state.task_results[dep_task_id]
                if dep_result.status == TaskStatus.SUCCESS:
                    resolved[f"{dep_task_id}_output"] = dep_result.outputs
        
        return resolved
    
    def _get_executor(self, task: TaskDefinition) -> BaseExecutor:
        """Get appropriate executor for task type"""
        if task.task_type == TaskType.AGENT:
            raise NotImplementedError("Agent executor requires agent instance")
        
        return self.executors[task.task_type]
    
    def _build_dag(self, workflow_def: WorkflowDefinition) -> WorkflowDAG:
        """Build DAG from workflow definition"""
        dag = WorkflowDAG(workflow_def.workflow_id)
        
        for task in workflow_def.tasks:
            dag.add_task(task)
        
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
