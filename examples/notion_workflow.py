"""
Complete integration example with Notion documentation.

Demonstrates:
1. Workflow execution
2. Kafka event publishing
3. State persistence
4. Notion documentation sync

Prerequisites:
- Kafka running on localhost:9092
- Notion workspace with two databases:
  - Workflow Database (for workflow definitions)
  - Execution Database (for execution logs)
- Environment variables set:
  - NEXUS_RAY_NOTION__ENABLED=true
  - NEXUS_RAY_NOTION__API_KEY=your_api_key
  - NEXUS_RAY_NOTION__WORKFLOW_DATABASE_ID=your_workflow_db_id
  - NEXUS_RAY_NOTION__EXECUTION_DATABASE_ID=your_execution_db_id
"""

import asyncio
from loguru import logger

from src.core.config import get_settings
from src.core.orchestrator_enhanced import EnhancedOrchestrator
from src.core.state_manager import StateManager
from src.messaging import KafkaClient
from src.sdk import WorkflowBuilder


async def main():
    """Run example with Notion integration"""
    
    settings = get_settings()
    
    print("=" * 80)
    print("Nexus Ray Framework - Notion Integration Example")
    print("=" * 80)
    print()
    
    # Check Notion configuration
    if settings.notion.enabled:
        logger.info("✅ Notion integration enabled")
        logger.info(f"   Workflow DB: {settings.notion.workflow_database_id[:8]}...")
        logger.info(f"   Execution DB: {settings.notion.execution_database_id[:8]}...")
    else:
        logger.warning("⚠️  Notion integration disabled (set NEXUS_RAY_NOTION__ENABLED=true)")
    print()
    
    # Initialize components
    kafka_client = None
    state_manager = None
    
    try:
        # Kafka client (optional)
        if settings.kafka.bootstrap_servers:
            kafka_client = KafkaClient()
            await kafka_client.start()
            logger.info("✅ Kafka client started")
    except Exception as e:
        logger.warning(f"Kafka not available: {e}")
    
    try:
        # State manager
        state_manager = StateManager()
        logger.info("✅ State manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize state manager: {e}")
    
    # Create orchestrator
    orchestrator = EnhancedOrchestrator(
        kafka_client=kafka_client,
        state_manager=state_manager
    )
    
    # Build a sample workflow
    logger.info("=== Creating Sample Workflow ===")
    
    workflow = (
        WorkflowBuilder("notion_demo_workflow")
        .set_description("Sample workflow to demonstrate Notion integration")
        .add_task(
            task_id="task1",
            name="Data Analysis Task",
            task_type="llm",
            description="Analyze sample data and generate insights",
            inputs={"data": "sample_dataset"},
            timeout_seconds=30
        )
        .add_task(
            task_id="task2",
            name="Report Generation",
            task_type="tool",
            description="Generate formatted report from analysis",
            depends_on=["task1"],
            timeout_seconds=30
        )
        .add_task(
            task_id="task3",
            name="Quality Review",
            task_type="human",
            description="Human review of generated report",
            depends_on=["task2"],
            timeout_seconds=60
        )
        .compile()
    )
    
    logger.info(f"Workflow created: {workflow.workflow_id}")
    logger.info(f"  Tasks: {len(workflow.tasks)}")
    logger.info(f"  Description: {workflow.description}")
    print()
    
    # Execute workflow
    logger.info("=== Executing Workflow ===")
    logger.info("Check your Notion workspace for real-time updates!")
    print()
    
    try:
        state = await orchestrator.execute_workflow(workflow)
        
        print()
        logger.info("=== Execution Complete ===")
        logger.info(f"Status: {state.status}")
        logger.info(f"Completed: {len(state.completed_tasks)}/{len(workflow.tasks)} tasks")
        logger.info(f"Duration: {(state.completed_at - state.started_at).total_seconds():.2f}s")
        
        if settings.notion.enabled:
            print()
            logger.info("📝 Check Notion for:")
            logger.info("   1. Workflow definition page")
            logger.info("   2. Execution log with task results")
            logger.info("   3. Progress updates throughout execution")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
    
    # Cleanup
    if kafka_client:
        await kafka_client.close()
        logger.info("Kafka client closed")


if __name__ == "__main__":
    asyncio.run(main())
