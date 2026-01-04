"""
DAG (Directed Acyclic Graph) workflow engine using NetworkX.

Handles workflow construction, validation, and topological execution ordering.
"""

from typing import List, Dict, Set, Optional
import networkx as nx
from loguru import logger

from src.core.task import TaskDefinition, TaskStatus


class WorkflowDAGError(Exception):
    """Base exception for DAG-related errors"""
    pass


class CyclicDependencyError(WorkflowDAGError):
    """Raised when a cycle is detected in the DAG"""
    pass


class TaskNotFoundError(WorkflowDAGError):
    """Raised when a task is not found in the DAG"""
    pass


class WorkflowDAG:
    """
    Directed Acyclic Graph for workflow orchestration.
    
    Uses NetworkX for graph operations and topological sorting.
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.graph = nx.DiGraph()
        self._tasks: Dict[str, TaskDefinition] = {}
        logger.info(f"Initialized DAG for workflow {workflow_id}")
    
    def add_task(self, task: TaskDefinition) -> None:
        """
        Add a task to the DAG.
        
        Args:
            task: TaskDefinition to add
            
        Raises:
            ValueError: If task already exists
        """
        if task.task_id in self._tasks:
            raise ValueError(f"Task {task.task_id} already exists in DAG")
        
        self._tasks[task.task_id] = task
        self.graph.add_node(task.task_id, task=task)
        
        logger.debug(f"Added task {task.task_id} ({task.name}) to DAG")
    
    def add_dependency(self, from_task_id: str, to_task_id: str) -> None:
        """
        Add a dependency edge (from_task must complete before to_task).
        
        Args:
            from_task_id: Task that must complete first
            to_task_id: Task that depends on from_task
            
        Raises:
            TaskNotFoundError: If either task doesn't exist
            CyclicDependencyError: If adding creates a cycle
        """
        if from_task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {from_task_id} not found")
        if to_task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {to_task_id} not found")
        
        # Add edge
        self.graph.add_edge(from_task_id, to_task_id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            # Remove the problematic edge
            self.graph.remove_edge(from_task_id, to_task_id)
            raise CyclicDependencyError(
                f"Adding dependency {from_task_id} -> {to_task_id} creates a cycle"
            )
        
        logger.debug(f"Added dependency: {from_task_id} -> {to_task_id}")
    
    def validate(self) -> bool:
        """
        Validate the DAG structure.
        
        Returns:
            True if DAG is valid
            
        Raises:
            WorkflowDAGError: If DAG is invalid
        """
        # Check if empty
        if len(self._tasks) == 0:
            raise WorkflowDAGError("DAG is empty")
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            raise CyclicDependencyError("DAG contains cycles")
        
        # Check if all dependencies exist
        for task_id, task in self._tasks.items():
            for dep in task.depends_on:
                if dep not in self._tasks:
                    raise TaskNotFoundError(
                        f"Task {task_id} depends on non-existent task {dep}"
                    )
        
        logger.info(f"DAG validation successful: {len(self._tasks)} tasks")
        return True
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get topological execution order with parallel batches.
        
        Returns:
            List of batches, where each batch contains task IDs that can run in parallel
            
        Example:
            [[task1], [task2, task3], [task4]]
            - task1 runs first
            - task2 and task3 can run in parallel after task1
            - task4 runs after task2 and task3 complete
        """
        try:
            # Get all generations (levels) in the DAG
            generations = list(nx.topological_generations(self.graph))
            
            logger.debug(f"Execution order: {len(generations)} batches")
            for i, batch in enumerate(generations):
                logger.debug(f"  Batch {i}: {batch}")
            
            return generations
            
        except nx.NetworkXError as e:
            raise WorkflowDAGError(f"Failed to compute execution order: {e}")
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """
        Get tasks that are ready to execute (all dependencies met).
        
        Args:
            completed_tasks: Set of task IDs that have completed
            
        Returns:
            List of task IDs ready to execute
        """
        ready = []
        
        for task_id in self._tasks:
            # Skip if already completed
            if task_id in completed_tasks:
                continue
            
            # Check if all dependencies are completed
            dependencies = list(self.graph.predecessors(task_id))
            if all(dep in completed_tasks for dep in dependencies):
                ready.append(task_id)
        
        return ready
    
    def get_task(self, task_id: str) -> TaskDefinition:
        """Get task definition by ID"""
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return self._tasks[task_id]
    
    def get_all_tasks(self) -> List[TaskDefinition]:
        """Get all task definitions"""
        return list(self._tasks.values())
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """Get list of tasks that this task depends on"""
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return list(self.graph.predecessors(task_id))
    
    def get_task_dependents(self, task_id: str) -> List[str]:
        """Get list of tasks that depend on this task"""
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return list(self.graph.successors(task_id))
    
    def get_root_tasks(self) -> List[str]:
        """Get tasks with no dependencies (entry points)"""
        return [
            task_id for task_id in self._tasks
            if self.graph.in_degree(task_id) == 0
        ]
    
    def get_leaf_tasks(self) -> List[str]:
        """Get tasks with no dependents (exit points)"""
        return [
            task_id for task_id in self._tasks
            if self.graph.out_degree(task_id) == 0
        ]
    
    @property
    def task_count(self) -> int:
        """Total number of tasks in the DAG"""
        return len(self._tasks)
    
    @property
    def is_valid(self) -> bool:
        """Check if DAG is valid without raising exceptions"""
        try:
            self.validate()
            return True
        except WorkflowDAGError:
            return False
    
    def to_dict(self) -> Dict:
        """Export DAG to dictionary representation"""
        return {
            "workflow_id": self.workflow_id,
            "tasks": [task.dict() for task in self._tasks.values()],
            "edges": [
                {"from": u, "to": v}
                for u, v in self.graph.edges()
            ],
            "task_count": self.task_count,
        }
    
    def visualize_ascii(self) -> str:
        """
        Create simple ASCII visualization of the DAG.
        
        Returns:
            ASCII art representation
        """
        lines = [f"Workflow DAG: {self.workflow_id}"]
        lines.append(f"Tasks: {self.task_count}")
        lines.append("")
        
        execution_order = self.get_execution_order()
        for i, batch in enumerate(execution_order):
            lines.append(f"Batch {i}:")
            for task_id in batch:
                task = self._tasks[task_id]
                lines.append(f"  - {task_id} ({task.name})")
        
        return "\n".join(lines)
