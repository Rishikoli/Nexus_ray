"""
Notion integration for workflow documentation.

Automatically syncs workflows, executions, and results to Notion databases.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from loguru import logger

try:
    from notion_client import AsyncClient
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    logger.warning("notion-client not installed. Notion sync will be disabled.")

from src.core.config import get_settings
from src.core.task import WorkflowDefinition, TaskResult, TaskStatus


class NotionSync:
    """
    Syncs workflow documentation to Notion.
    
    Features:
    - Auto-create workflow pages on submission
    - Update execution status in real-time
    - Log task results and metrics
    - Create audit trail in Notion
    """
    
    def __init__(self):
        """Initialize Notion client"""
        self.settings = get_settings()
        self.notion_config = self.settings.notion
        self.client: Optional[AsyncClient] = None
        
        if not NOTION_AVAILABLE:
            logger.warning("Notion client not available - sync disabled")
            return
            
        if not self.notion_config.enabled:
            logger.info("Notion sync disabled in configuration")
            return
            
        if not self.notion_config.api_key:
            logger.warning("Notion API key not configured")
            return
            
        # Initialize Notion client
        try:
            self.client = AsyncClient(auth=self.notion_config.api_key)
            logger.info("Notion sync initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Notion client: {e}")
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if Notion sync is enabled and configured"""
        return (
            NOTION_AVAILABLE and 
            self.notion_config.enabled and 
            self.client is not None
        )
    
    async def sync_workflow_definition(
        self,
        workflow: WorkflowDefinition
    ) -> Optional[str]:
        """
        Create Notion page for workflow definition.
        
        Args:
            workflow: Workflow definition to sync
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None
            
        try:
            # Prepare workflow documentation
            properties = {
                "Name": {"title": [{"text": {"content": workflow.name}}]},
                "Workflow ID": {"rich_text": [{"text": {"content": workflow.workflow_id}}]},
                "Total Tasks": {"number": len(workflow.tasks)},
                "Created": {"date": {"start": datetime.now().isoformat()}},
                "Status": {"select": {"name": "Pending"}}
            }
            
            # Create task list for description
            task_list = "\n".join([
                f"- **{task.task_id}** ({task.task_type.value}): {task.description or 'No description'}"
                for task in workflow.tasks.values()
            ])
            
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Workflow Overview"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": workflow.description or "No description provided"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Tasks"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": task_list}}]
                    }
                }
            ]
            
            # Create page in workflow database
            response = await self.client.pages.create(
                parent={"database_id": self.notion_config.workflow_database_id},
                properties=properties,
                children=children
            )
            
            page_id = response["id"]
            logger.info(f"Created Notion page for workflow {workflow.workflow_id}: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to sync workflow to Notion: {e}")
            return None
    
    async def sync_execution_start(
        self,
        workflow_id: str,
        workflow_name: str,
        started_at: datetime
    ) -> Optional[str]:
        """
        Create execution log entry in Notion.
        
        Args:
            workflow_id: Workflow ID
            workflow_name: Workflow name
            started_at: Execution start time
            
        Returns:
            Notion page ID if successful
        """
        if not self.is_enabled():
            return None
            
        try:
            properties = {
                "Name": {"title": [{"text": {"content": f"{workflow_name} - Execution"}}]},
                "Workflow ID": {"rich_text": [{"text": {"content": workflow_id}}]},
                "Started": {"date": {"start": started_at.isoformat()}},
                "Status": {"select": {"name": "Running"}},
                "Progress": {"number": 0}
            }
            
            response = await self.client.pages.create(
                parent={"database_id": self.notion_config.execution_database_id},
                properties=properties
            )
            
            page_id = response["id"]
            logger.info(f"Created execution log for {workflow_id}: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create execution log: {e}")
            return None
    
    async def update_execution_progress(
        self,
        page_id: str,
        completed_tasks: int,
        total_tasks: int,
        status: str = "Running"
    ):
        """
        Update execution progress in Notion.
        
        Args:
            page_id: Notion page ID
            completed_tasks: Number of completed tasks
            total_tasks: Total number of tasks
            status: Execution status
        """
        if not self.is_enabled() or not page_id:
            return
            
        try:
            progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
            
            await self.client.pages.update(
                page_id=page_id,
                properties={
                    "Progress": {"number": progress},
                    "Status": {"select": {"name": status}},
                    "Completed Tasks": {"number": completed_tasks}
                }
            )
            
            logger.debug(f"Updated execution progress: {completed_tasks}/{total_tasks}")
            
        except Exception as e:
            logger.error(f"Failed to update execution progress: {e}")
    
    async def sync_execution_complete(
        self,
        page_id: str,
        workflow_id: str,
        status: str,
        completed_at: datetime,
        task_results: Dict[str, TaskResult],
        error_message: Optional[str] = None
    ):
        """
        Mark execution as complete in Notion.
        
        Args:
            page_id: Notion page ID
            workflow_id: Workflow ID
            status: Final status (completed/failed)
            completed_at: Completion time
            task_results: Map of task results
            error_message: Error message if failed
        """
        if not self.is_enabled() or not page_id:
            return
            
        try:
            # Update properties
            properties = {
                "Status": {"select": {"name": status.capitalize()}},
                "Completed": {"date": {"start": completed_at.isoformat()}},
                "Progress": {"number": 100 if status == "completed" else 0}
            }
            
            if error_message:
                properties["Error"] = {"rich_text": [{"text": {"content": error_message[:2000]}}]}
            
            await self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            # Append task results as blocks
            result_blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Execution Results"}}]
                    }
                }
            ]
            
            for task_id, result in task_results.items():
                status_emoji = "✅" if result.status == TaskStatus.SUCCESS else "❌"
                result_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": f"{status_emoji} {task_id}: {result.status.value}"}
                        }]
                    }
                })
            
            await self.client.blocks.children.append(
                block_id=page_id,
                children=result_blocks
            )
            
            logger.info(f"Execution {workflow_id} marked as {status} in Notion")
            
        except Exception as e:
            logger.error(f"Failed to sync execution completion: {e}")
    
    async def add_task_result(
        self,
        page_id: str,
        task_id: str,
        task_result: TaskResult
    ):
        """
        Add individual task result to execution log.
        
        Args:
            page_id: Notion page ID
            task_id: Task ID
            task_result: Task execution result
        """
        if not self.is_enabled() or not page_id:
            return
            
        try:
            status_emoji = {
                TaskStatus.SUCCESS: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.PENDING: "⏳",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.TIMEOUT: "⏱️",
                TaskStatus.SKIPPED: "⏭️"
            }.get(task_result.status, "❓")
            
            duration = f" ({task_result.metadata.get('duration_ms', 0)}ms)" if task_result.metadata else ""
            
            content = f"{status_emoji} **{task_id}**: {task_result.status.value}{duration}"
            
            await self.client.blocks.children.append(
                block_id=page_id,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }]
            )
            
        except Exception as e:
            logger.error(f"Failed to add task result to Notion: {e}")


# Singleton instance
_notion_sync: Optional[NotionSync] = None


def get_notion_sync() -> NotionSync:
    """Get global NotionSync instance"""
    global _notion_sync
    if _notion_sync is None:
        _notion_sync = NotionSync()
    return _notion_sync
