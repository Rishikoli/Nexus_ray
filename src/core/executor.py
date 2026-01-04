"""
Base executor interfaces for task execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from src.core.task import TaskDefinition, TaskResult, TaskStatus


class ExecutorError(Exception):
    """Base exception for executor errors"""
    pass


class BaseExecutor(ABC):
    """
    Abstract base class for all task executors.
    
    Executors are responsible for running specific types of tasks
    (LLM, Tool, Human, etc.) and returning results.
    """
    
    def __init__(self, executor_id: str):
        self.executor_id = executor_id
        logger.debug(f"Initialized {self.__class__.__name__}: {executor_id}")
    
    @abstractmethod
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """
        Execute a task and return the result.
        
        Args:
            task: TaskDefinition to execute
            
        Returns:
            TaskResult with outputs and status
            
        Raises:
            ExecutorError: If execution fails
        """
        pass
    
    async def run_with_metrics(self, task: TaskDefinition) -> TaskResult:
        """
        Execute task with automatic timing, retries, and error handling.
        
        This is the main entry point that wrappers around execute().
        """
        import asyncio
        
        logger.info(f"Starting task {task.task_id} ({task.name})")
        
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        max_retries = getattr(task, 'max_retries', 3)
        timeout = getattr(task, 'timeout_seconds', None)
        
        for attempt in range(max_retries + 1):
            try:
                # Update retry count
                result.retry_count = attempt
                
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for task {task.task_id}")
                
                # Execute with timeout if specified
                if timeout:
                    execute_coro = self.execute(task)
                    task_result = await asyncio.wait_for(execute_coro, timeout=timeout)
                else:
                    task_result = await self.execute(task)
                
                # If we got here, execution was successful (or at least didn't raise)
                # Merge the returned result into our tracking result
                result.outputs = task_result.outputs
                result.status = task_result.status
                result.metrics.update(task_result.metrics)
                
                # Ensure status is set to SUCCESS if it was RUNNING
                if result.status == TaskStatus.RUNNING:
                    result.status = TaskStatus.SUCCESS
                
                break  # Success! Exit retry loop
            
            except asyncio.TimeoutError:
                error_msg = f"Task execution timed out after {timeout} seconds"
                logger.error(f"Task {task.task_id} failed: {error_msg}")
                result.error = error_msg
                result.status = TaskStatus.FAILED
                
                # If last attempt, don't fallback to loop
                if attempt == max_retries:
                    break
                    
            except Exception as e:
                logger.error(f"Task {task.task_id} failed (attempt {attempt}): {str(e)}", exc_info=True)
                result.error = str(e)
                result.status = TaskStatus.FAILED
                
                if attempt == max_retries:
                    break
        
        # Finalize timing
        result.completed_at = datetime.utcnow()
        if result.started_at:
            duration = (result.completed_at - result.started_at).total_seconds()
            result.duration_ms = int(duration * 1000)
        
        logger.info(
            f"Task {task.task_id} finished: {result.status} "
            f"({result.duration_ms}ms, {result.retry_count} retries)"
        )
        
        return result
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(executor_id='{self.executor_id}')"


class LLMExecutor(BaseExecutor):
    """
    Executor for LLM-based tasks with OpenVINO optimization.
    
    Features:
    - OpenVINO-optimized inference
    - Automatic prompt formatting
    - JSON output parsing
    - Token tracking
    """
    
    def __init__(self, executor_id: str = "llm_executor", model_name: Optional[str] = None):
        super().__init__(executor_id)
        self.model_name = model_name
        self.llm = None  # Lazy loading
    
    def _get_llm(self):
        """Lazy load LLM instance"""
        if self.llm is None:
            try:
                from src.llm import get_llm
                self.llm = get_llm(self.model_name or "mistral-7b-ov")
                logger.info(f"Loaded LLM: {self.llm}")
            except Exception as e:
                logger.error(f"Failed to load LLM: {e}")
                raise ExecutorError(f"LLM initialization failed: {e}")
        return self.llm
    
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """Execute LLM task"""
        from src.llm.prompts import create_task_prompt
        from src.llm.parser import parse_llm_output
        
        try:
            llm = self._get_llm()
            
            # Build prompt
            prompt = create_task_prompt(
                task_type=task.task_type.value,
                task_description=task.description or task.name,
                inputs=task.inputs,
                context=task.metadata.get("context") if task.metadata else None
            )
            
            logger.debug(f"LLM prompt length: {llm.count_tokens(prompt)} tokens")
            
            # Generate response
            response = llm.generate(
                prompt,
                max_tokens=task.metadata.get("max_tokens") if task.metadata else None,
                temperature=task.metadata.get("temperature") if task.metadata else None
            )
            
            # Parse output
            output_type = task.metadata.get("output_type", "text") if task.metadata else "text"
            parsed_output = parse_llm_output(response, output_type=output_type)
            
            # Track metrics
            input_tokens = llm.count_tokens(prompt)
            output_tokens = llm.count_tokens(response)
            
            metrics = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": llm.model_name
            }
            
            # Record to global store
            try:
                from src.core.metrics_store import metrics_store
                metrics_store.record_llm_call(input_tokens, output_tokens, success=True)
            except ImportError:
                pass  # Fallback if store not available (e.g. tests)
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.SUCCESS,
                outputs={"result": parsed_output, "raw_response": response},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            
            # Record failure
            try:
                from src.core.metrics_store import metrics_store
                metrics_store.record_llm_call(0, 0, success=False)
            except:
                pass
                
            raise ExecutorError(f"LLM execution failed: {e}")


class ToolExecutor(BaseExecutor):
    """
    Executor for tool-based tasks.
    
    Executes registered tools from the tool registry.
    """
    
    def __init__(self, executor_id: str = "tool_executor"):
        super().__init__(executor_id)
        self.tool_registry = None  # Will be ToolRegistry instance
    
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """Execute tool task"""
        # Placeholder for Phase 3
        logger.warning("ToolExecutor not fully implemented - placeholder execution")
        
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCESS,
            outputs={"placeholder": "Tool execution pending implementation"},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=0
        )


class HumanExecutor(BaseExecutor):
    """
    Executor for human-in-the-loop tasks.
    
    Pauses workflow and waits for human approval/input.
    """
    
    def __init__(self, executor_id: str = "human_executor"):
        super().__init__(executor_id)
    
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """
        Execute HITL task.
        
        This sets status to WAITING_HUMAN and requires external approval.
        """
        logger.info(f"Task {task.task_id} requires human approval")
        
        # In real implementation, this would:
        # 1. Send notification to approvers
        # 2. Wait for approval via API
        # 3. Resume with approved/rejected status
        
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.WAITING_HUMAN,
            outputs={
                "approval_required": True,
                "hitl_config": task.hitl_config
            },
            started_at=datetime.utcnow()
        )


class AgentExecutor(BaseExecutor):
    """
    Executor for custom agent tasks.
    
    Delegates to agent-specific execute() method.
    """
    
    def __init__(self, agent_instance, executor_id: Optional[str] = None):
        self.agent = agent_instance
        executor_id = executor_id or f"agent_{agent_instance.__class__.__name__}"
        super().__init__(executor_id)
    
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """Delegate to agent's execute method"""
        logger.info(f"Executing custom agent: {self.agent.__class__.__name__}")
        
        try:
            # Call agent's execute method
            outputs = await self.agent.execute(task.inputs)
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.SUCCESS,
                outputs=outputs,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise ExecutorError(f"Agent execution failed: {e}")
