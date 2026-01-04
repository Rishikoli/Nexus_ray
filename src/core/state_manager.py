"""
State persistence for workflows using SQLite/PostgreSQL.

Stores workflow execution state for recovery and auditing.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from src.core.task import TaskStatus, WorkflowDefinition
from src.core.config import get_settings

Base = declarative_base()


class WorkflowStateDB(Base):
    """Database model for workflow state"""
    
    __tablename__ = "workflow_states"
    
    workflow_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # running, completed, failed, cancelled
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Workflow definition
    workflow_definition = Column(JSON, nullable=False)
    
    # Execution state
    task_results = Column(JSON, nullable=True)
    completed_tasks = Column(JSON, nullable=True)  # List of task IDs
    failed_tasks = Column(JSON, nullable=True)
    
    # Metadata
    workflow_metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)


class TaskExecutionDB(Base):
    """Database model for individual task executions"""
    
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), nullable=False, index=True)
    task_id = Column(String(255), nullable=False)
    
    status = Column(SQLEnum(TaskStatus), nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Data
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Metrics
    retry_count = Column(Integer, default=0)
    metrics = Column(JSON, nullable=True)


class StateManager:
    """
    Manages workflow state persistence.
    
    Provides methods to save/load workflow state for recovery.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        settings = get_settings()
        self.database_url = database_url or settings.database.url
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"StateManager initialized with database: {self.database_url}")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def save_workflow_state(
        self,
        workflow_id: str,
        name: str,
        status: str,
        workflow_definition: WorkflowDefinition,
        task_results: Optional[Dict] = None,
        completed_tasks: Optional[List[str]] = None,
        failed_tasks: Optional[List[str]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save workflow state to database.
        
        Args:
            workflow_id: Workflow identifier
            name: Workflow name
            status: Current status
            workflow_definition: Workflow definition
            task_results: Task execution results
            completed_tasks: List of completed task IDs
            failed_tasks: List of failed task IDs
            started_at: Workflow start time
            completed_at: Workflow completion time
            error_message: Error message if failed
            metadata: Additional metadata
        """
        session = self.get_session()
        
        try:
            # Check if workflow exists
            workflow_state = session.query(WorkflowStateDB).filter_by(
                workflow_id=workflow_id
            ).first()
            
            if workflow_state:
                # Update existing
                workflow_state.status = status
                workflow_state.task_results = task_results or {}
                workflow_state.completed_tasks = completed_tasks or []
                workflow_state.failed_tasks = failed_tasks or []
                workflow_state.started_at = started_at
                workflow_state.completed_at = completed_at
                workflow_state.error_message = error_message
                workflow_state.workflow_metadata = metadata or {}
            else:
                # Create new
                workflow_state = WorkflowStateDB(
                    workflow_id=workflow_id,
                    name=name,
                    status=status,
                    workflow_definition=workflow_definition.dict(),
                    task_results=task_results or {},
                    completed_tasks=completed_tasks or [],
                    failed_tasks=failed_tasks or [],
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message=error_message,
                    workflow_metadata=metadata or {}
                )
                session.add(workflow_state)
            
            session.commit()
            logger.debug(f"Saved workflow state: {workflow_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save workflow state: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from database.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow state dict or None if not found
        """
        session = self.get_session()
        
        try:
            workflow_state = session.query(WorkflowStateDB).filter_by(
                workflow_id=workflow_id
            ).first()
            
            if not workflow_state:
                return None
            
            return {
                "workflow_id": workflow_state.workflow_id,
                "name": workflow_state.name,
                "status": workflow_state.status,
                "workflow_definition": workflow_state.workflow_definition,
                "task_results": workflow_state.task_results,
                "completed_tasks": workflow_state.completed_tasks,
                "failed_tasks": workflow_state.failed_tasks,
                "started_at": workflow_state.started_at,
                "completed_at": workflow_state.completed_at,
                "error_message": workflow_state.error_message,
                "metadata": workflow_state.workflow_metadata
            }
            
        finally:
            session.close()
    
    def save_task_execution(
        self,
        workflow_id: str,
        task_id: str,
        status: TaskStatus,
        inputs: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        retry_count: int = 0,
        metrics: Optional[Dict] = None
    ) -> None:
        """Save individual task execution to database"""
        session = self.get_session()
        
        try:
            task_exec = TaskExecutionDB(
                workflow_id=workflow_id,
                task_id=task_id,
                status=status,
                inputs=inputs,
                outputs=outputs,
                error=error,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                retry_count=retry_count,
                metrics=metrics
            )
            
            session.add(task_exec)
            session.commit()
            logger.debug(f"Saved task execution: {task_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save task execution: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def get_task_executions(
        self,
        workflow_id: str
    ) -> List[Dict[str, Any]]:
        """Get all task executions for a workflow"""
        session = self.get_session()
        
        try:
            executions = session.query(TaskExecutionDB).filter_by(
                workflow_id=workflow_id
            ).all()
            
            return [
                {
                    "task_id": e.task_id,
                    "status": e.status.value,
                    "started_at": e.started_at,
                    "completed_at": e.completed_at,
                    "duration_ms": e.duration_ms,
                    "inputs": e.inputs,
                    "outputs": e.outputs,
                    "error": e.error,
                    "retry_count": e.retry_count,
                    "metrics": e.metrics
                }
                for e in executions
            ]
            
        finally:
            session.close()
    
    def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflows with optional status filter.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of results
            
        Returns:
            List of workflow summaries
        """
        session = self.get_session()
        
        try:
            query = session.query(WorkflowStateDB)
            
            if status:
                query = query.filter_by(status=status)
            
            workflows = query.order_by(
                WorkflowStateDB.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "workflow_id": w.workflow_id,
                    "name": w.name,
                    "status": w.status,
                    "created_at": w.created_at,
                    "started_at": w.started_at,
                    "completed_at": w.completed_at
                }
                for w in workflows
            ]
            
        finally:
            session.close()
    
    def cleanup_old_workflows(self, days: int = 30) -> int:
        """
        Delete workflow states older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted workflows
        """
        session = self.get_session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted = session.query(WorkflowStateDB).filter(
                WorkflowStateDB.completed_at < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted} old workflows")
            
            return deleted
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup workflows: {e}")
            raise
        finally:
            session.close()


from datetime import timedelta  # Add this import at top
