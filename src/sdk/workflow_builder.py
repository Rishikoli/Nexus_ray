"""
SDK for building workflows with a fluent API.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

from src.core.task import TaskDefinition, TaskType, WorkflowDefinition
from loguru import logger


class WorkflowBuilder:
    """
    Fluent API for building workflows.
    
    Example:
        workflow = WorkflowBuilder("protein_drug_discovery")
        workflow.add_task("validate", ValidatorAgent(), depends_on=[])
        workflow.add_task("predict", PredictorAgent(), depends_on=["validate"])
        workflow.compile()
    """
    
    def __init__(self, name: str, workflow_id: Optional[str] = None):
        self.name = name
        self.workflow_id = workflow_id or f"wf-{uuid.uuid4().hex[:8]}"
        self.description: Optional[str] = None
        self.tasks: List[TaskDefinition] = []
        self.metadata: Dict[str, Any] = {}
        self.timeout_seconds: Optional[int] = None
        
        logger.debug(f"Initialized WorkflowBuilder: {self.workflow_id}")
    
    def set_description(self, description: str) -> 'WorkflowBuilder':
        """Set workflow description"""
        self.description = description
        return self
    
    def set_timeout(self, timeout_seconds: int) -> 'WorkflowBuilder':
        """Set workflow-level timeout"""
        self.timeout_seconds = timeout_seconds
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'WorkflowBuilder':
        """Add metadata to workflow"""
        self.metadata[key] = value
        return self
    
    def add_task(
        self,
        task_id: str,
        task_type: TaskType,
        name: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        executor_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None,
        hitl_config: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowBuilder':
        """
        Add a task to the workflow.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task (LLM, TOOL, HUMAN, AGENT)
            name: Human-readable name (defaults to task_id)
            depends_on: List of task IDs this task depends on
            inputs: Input data for the task
            executor_config: Configuration for the executor
            max_retries: Maximum retry attempts
            timeout_seconds: Task timeout
            
        Returns:
            Self for method chaining
        """
        task = TaskDefinition(
            task_id=task_id,
            name=name or task_id,
            task_type=task_type,
            depends_on=depends_on or [],
            inputs=inputs or {},
            executor_config=executor_config or {},
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            hitl_config=hitl_config
        )
        
        self.tasks.append(task)
        logger.debug(f"Added task: {task_id} ({task_type})")
        
        return self
    
    def add_llm_task(
        self,
        task_id: str,
        prompt: str,
        model: str = "mistral-7b-ov",
        temperature: float = 0.7,
        max_tokens: int = 500,
        depends_on: Optional[List[str]] = None,
        **kwargs
    ) -> 'WorkflowBuilder':
        """
        Convenience method to add an LLM task.
        
        Args:
            task_id: Task identifier
            prompt: LLM prompt template
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            depends_on: Task dependencies
            **kwargs: Additional task parameters
            
        Returns:
            Self for method chaining
        """
        executor_config = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        return self.add_task(
            task_id=task_id,
            task_type=TaskType.LLM,
            depends_on=depends_on,
            executor_config=executor_config,
            **kwargs
        )
    
    def add_tool_task(
        self,
        task_id: str,
        tool_name: str,
        tool_inputs: Optional[Dict] = None,
        depends_on: Optional[List[str]] = None,
        **kwargs
    ) -> 'WorkflowBuilder':
        """
        Convenience method to add a tool task.
        
        Args:
            task_id: Task identifier
            tool_name: Name of registered tool
            tool_inputs: Inputs for the tool
            depends_on: Task dependencies
            **kwargs: Additional task parameters
            
        Returns:
            Self for method chaining
        """
        executor_config = {
            "tool_name": tool_name
        }
        
        return self.add_task(
            task_id=task_id,
            task_type=TaskType.TOOL,
            inputs=tool_inputs or {},
            depends_on=depends_on,
            executor_config=executor_config,
            **kwargs
        )
    
    def add_hitl_gate(
        self,
        task_id: str,
        after: str,
        condition: Optional[Callable] = None,
        approvers: Optional[List[str]] = None,
        notification_channels: Optional[List[str]] = None,
        **kwargs
    ) -> 'WorkflowBuilder':
        """
        Add a human-in-the-loop approval gate.
        
        Args:
            task_id: Task identifier
            after: Task ID after which this gate should run
            condition: Optional condition function (if None, always triggers)
            approvers: List of email addresses or user IDs
            notification_channels: Channels for notifications (email, slack, etc.)
            **kwargs: Additional task parameters
            
        Returns:
            Self for method chaining
        """
        hitl_config = {
            "approvers": approvers or [],
            "notification_channels": notification_channels or ["email"],
            "condition": condition
        }
        
        return self.add_task(
            task_id=task_id,
            task_type=TaskType.HUMAN,
            name=f"HITL Gate after {after}",
            depends_on=[after],
            hitl_config=hitl_config,
            **kwargs
        )
    
    def compile(self) -> WorkflowDefinition:
        """
        Compile the workflow into a WorkflowDefinition.
        
        Returns:
            WorkflowDefinition ready for execution
        """
        if not self.tasks:
            raise ValueError("Workflow must have at least one task")
        
        workflow_def = WorkflowDefinition(
            workflow_id=self.workflow_id,
            name=self.name,
            description=self.description,
            tasks=self.tasks,
            timeout_seconds=self.timeout_seconds,
            metadata=self.metadata
        )
        
        logger.info(
            f"Compiled workflow: {self.workflow_id} "
            f"({len(self.tasks)} tasks)"
        )
        
        return workflow_def
    
    def visualize(self) -> str:
        """
        Generate ASCII visualization of the workflow.
        
        Returns:
            ASCII art representation
        """
        lines = [f"Workflow: {self.name} ({self.workflow_id})"]
        lines.append(f"Tasks: {len(self.tasks)}")
        lines.append("")
        
        for task in self.tasks:
            deps = ", ".join(task.depends_on) if task.depends_on else "none"
            lines.append(f"  [{task.task_type}] {task.task_id}")
            lines.append(f"    Depends on: {deps}")
        
        return "\n".join(lines)


# Example workflow builders for reference agents

def build_protein_drug_workflow() -> WorkflowDefinition:
    """
    Build the Protein-Drug Discovery workflow.
    
    Returns:
        Compiled workflow definition
    """
    workflow = WorkflowBuilder(
        name="protein_drug_discovery",
        workflow_id="protein_drug_discovery"
    )
    
    workflow.set_description(
        "Analyzes protein-drug interactions and predicts drugability"
    )
    
    # Task 1: Input validation
    workflow.add_task(
        task_id="validate",
        task_type=TaskType.AGENT,
        name="Input Validator",
        inputs={"validate_sequence": True, "validate_drug": True}
    )
    
    # Task 2: Structure prediction
    workflow.add_task(
        task_id="predict",
        task_type=TaskType.AGENT,
        name="Structure Predictor",
        depends_on=["validate"],
        timeout_seconds=30
    )
    
    # Task 3: Quality assessment
    workflow.add_task(
        task_id="quality",
        task_type=TaskType.AGENT,
        name="Quality Assessor",
        depends_on=["predict"]
    )
    
    # Task 4: Binding site identification
    workflow.add_task(
        task_id="binding_site",
        task_type=TaskType.AGENT,
        name="Binding Site Identifier",
        depends_on=["quality"]
    )
    
    # Task 5: Molecular docking
    workflow.add_task(
        task_id="docking",
        task_type=TaskType.AGENT,
        name="Molecular Docking",
        depends_on=["binding_site"],
        timeout_seconds=60
    )
    
    # Task 6: Binding & safety evaluation
    workflow.add_task(
        task_id="eval",
        task_type=TaskType.AGENT,
        name="Binding & Safety Evaluator",
        depends_on=["docking"]
    )
    
    # Task 7: Drugability scoring
    workflow.add_llm_task(
        task_id="score",
        prompt="Score drugability based on binding affinity and toxicity",
        model="mistral-7b-ov",
        depends_on=["eval"]
    )
    
    # HITL gate
    workflow.add_hitl_gate(
        task_id="expert_review",
        after="score",
        approvers=["expert@pharma.com"],
        notification_channels=["slack", "email"]
    )
    
    return workflow.compile()


def build_semiconductor_workflow() -> WorkflowDefinition:
    """
    Build the Semiconductor Yield Optimization workflow.
    
    Returns:
        Compiled workflow definition
    """
    workflow = WorkflowBuilder(
        name="semiconductor_yield",
        workflow_id="semiconductor_yield"
    )
    
    workflow.set_description(
        "Analyzes wafer defects and optimizes fabrication yield"
    )
    
    # Parallel paths: Image analysis + Sensor analysis
    
    # Image path
    workflow.add_task(
        task_id="defect_analysis",
        task_type=TaskType.AGENT,
        name="Defect Analysis",
        timeout_seconds=30
    )
    
    workflow.add_task(
        task_id="classify",
        task_type=TaskType.AGENT,
        name="Defect Classifier",
        depends_on=["defect_analysis"]
    )
    
    # Sensor path
    workflow.add_task(
        task_id="process_intel",
        task_type=TaskType.AGENT,
        name="Process Intelligence"
    )
    
    # Converge
    workflow.add_task(
        task_id="yield_pred",
        task_type=TaskType.AGENT,
        name="Yield Impact Predictor",
        depends_on=["classify"]
    )
    
    workflow.add_llm_task(
        task_id="rca",
        prompt="Analyze root cause of defects based on correlation",
        model="mistral-7b-ov",
        name="Root Cause Analyzer",
        depends_on=["yield_pred", "process_intel"]
    )
    
    workflow.add_llm_task(
        task_id="aggregate",
        prompt="Synthesize yield analysis and prioritize issues",
        model="mistral-7b-ov",
        name="Yield Aggregator",
        depends_on=["rca"]
    )
    
    workflow.add_llm_task(
        task_id="optimize",
        prompt="Recommend recipe optimizations with trade-off analysis",
        model="mistral-7b-ov",
        name="Recipe Intelligence",
        depends_on=["aggregate"]
    )
    
    # HITL - always required before deployment
    workflow.add_hitl_gate(
        task_id="engineer_approval",
        after="optimize",
        approvers=["engineer@fab.com"],
        notification_channels=["email", "dashboard"]
    )
    
    workflow.add_task(
        task_id="deploy",
        task_type=TaskType.TOOL,
        name="Recipe Deployment",
        depends_on=["engineer_approval"]
    )
    
    return workflow.compile()
