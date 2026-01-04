"""
Complete integration example showing all components working together.

This demonstrates:
- Configuration loading
- Kafka messaging
- State persistence
- Enhanced orchestrator
- Workflow execution with events
"""

import asyncio
from loguru import logger

from src.core.config import get_settings
from src.core.orchestrator_enhanced import EnhancedOrchestrator
from src.core.state_manager import StateManager
from src.messaging import KafkaClient, KafkaConfig, subscribe
from src.sdk import WorkflowBuilder
from src.core.task import TaskType


# Example: Protein-Drug Discovery Workflow with Full Integration

async def run_protein_drug_workflow_integrated():
    """
    Complete example of protein-drug workflow with all integrations.
    """
    logger.info("=== Starting Integrated Protein-Drug Workflow ===")
    
    # 1. Load configuration
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Kafka enabled: {settings.kafka.bootstrap_servers}")
    
    # 2. Initialize Kafka client
    kafka_config = KafkaConfig(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        client_id=settings.kafka.client_id,
        group_id=settings.kafka.group_id
    )
    kafka_client = KafkaClient(kafka_config)
    
    # 3. Initialize state manager
    state_manager = StateManager(database_url=settings.database.url)
    
    # 4. Set up event listeners
    @subscribe(topic="workflow.events")
    async def on_workflow_event(topic: str, message: dict):
        """Listen to all workflow events"""
        event_type = message.get('type')
        workflow_id = message.get('workflow_id')
        
        logger.info(f"📢 Event: {event_type} for workflow {workflow_id}")
        
        if event_type == "workflow_started":
            logger.info(f"  ▶️  Workflow started: {message.get('workflow_name')}")
        elif event_type == "task_completed":
            task_id = message.get('task_id')
            duration = message.get('duration_ms', 0)
            logger.info(f"  ✅ Task completed: {task_id} ({duration}ms)")
        elif event_type == "workflow_completed":
            duration = message.get('duration_seconds', 0)
            logger.info(f"  🎉 Workflow completed in {duration:.2f}s")
    
    @subscribe(topic="llm.activity")
    async def on_llm_activity(topic: str, message: dict):
        """Listen to LLM activity"""
        event_type = message.get('type')
        agent_id = message.get('agent_id')
        
        if event_type == "llm_call_started":
            logger.info(f"🧠 LLM call started: {agent_id}")
        elif event_type == "llm_call_completed":
            tokens = message.get('tokens_used', 0)
            latency = message.get('latency_ms', 0)
            logger.info(f"🧠 LLM call completed: {tokens} tokens, {latency}ms")
    
    @subscribe(topic="hitl.requests")
    async def on_hitl_request(topic: str, message: dict):
        """Listen to HITL requests"""
        task_id = message.get('task_id')
        logger.warning(f"👤 HITL Approval Required for task: {task_id}")
    
    # 5. Start Kafka client
    await kafka_client.start()
    logger.info("Kafka client started")
    
    # 6. Build workflow
    workflow = WorkflowBuilder(
        name="protein_drug_discovery_integrated",
        workflow_id="pd-demo-001"
    )
    
    workflow.set_description("Integrated protein-drug discovery with full observability")
    
    # Task 1: Input Validation
    workflow.add_task(
        task_id="validate",
        task_type=TaskType.TOOL,
        name="Input Validator",
        inputs={
            "protein_sequence": "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
            "drug_smiles": "CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O"
        }
    )
    
    # Task 2: Structure Prediction
    workflow.add_llm_task(
        task_id="predict",
        prompt="Predict protein structure from sequence",
        model="mistral-7b-ov",
        depends_on=["validate"],
        timeout_seconds=30
    )
    
    # Task 3: Quality Assessment
    workflow.add_llm_task(
        task_id="quality",
        prompt="Assess structure quality and confidence",
        model="mistral-7b-ov",
        depends_on=["predict"]
    )
    
    # Task 4: Binding Site Identification
    workflow.add_task(
        task_id="binding_site",
        task_type=TaskType.TOOL,
        name="Binding Site Identifier",
        depends_on=["quality"]
    )
    
    # Task 5: Molecular Docking
    workflow.add_task(
        task_id="docking",
        task_type=TaskType.TOOL,
        name="Molecular Docking",
        depends_on=["binding_site"],
        timeout_seconds=60
    )
    
    # Task 6: Scoring
    workflow.add_llm_task(
        task_id="score",
        prompt="Score drugability based on binding and safety",
        model="mistral-7b-ov",
        depends_on=["docking"]
    )
    
    # Task 7: HITL Approval Gate
    workflow.add_hitl_gate(
        task_id="expert_review",
        after="score",
        approvers=["expert@pharma.com"],
        notification_channels=["slack", "email"]
    )
    
    workflow_def = workflow.compile()
    logger.info(f"Workflow compiled: {len(workflow_def.tasks)} tasks")
    
    # 7. Create enhanced orchestrator
    orchestrator = EnhancedOrchestrator(
        kafka_client=kafka_client,
        state_manager=state_manager
    )
    
    # 8. Execute workflow
    logger.info("🚀 Starting workflow execution...")
    
    try:
        state = await orchestrator.execute_workflow(
            workflow_def,
            inputs={
                "researcher": "John Doe",
                "project": "NSAID Optimization"
            }
        )
        
        logger.info(f"✅ Workflow completed: {state.status}")
        logger.info(f"   Progress: {state.progress_percentage:.1f}%")
        logger.info(f"   Completed: {len(state.completed_tasks)} tasks")
        logger.info(f"   Failed: {len(state.failed_tasks)} tasks")
        
        # 9. Check persisted state
        loaded_state = state_manager.load_workflow_state(workflow_def.workflow_id)
        if loaded_state:
            logger.info(f"💾 State persisted successfully")
            logger.info(f"   Status: {loaded_state['status']}")
        
        # 10. Get task execution history
        task_executions = state_manager.get_task_executions(workflow_def.workflow_id)
        logger.info(f"📊 Task executions: {len(task_executions)}")
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        await kafka_client.stop()
        logger.info("Kafka client stopped")
    
    logger.info("=== Integration Example Complete ===")


# Example: Simple workflow without Kafka/Persistence (for testing)

async def run_simple_workflow():
    """
    Simple workflow without Kafka/persistence for quick testing.
    """
    from src.core.orchestrator import WorkflowOrchestrator
    
    logger.info("=== Running Simple Workflow ===")
    
    # Build workflow
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
    
    # Execute with basic orchestrator
    orchestrator = WorkflowOrchestrator()
    state = await orchestrator.execute_workflow(workflow_def)
    
    logger.info(f"Workflow status: {state.status}")
    logger.info("=== Simple Workflow Complete ===")


# Main entry point

async def main():
    """Main entry point"""
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Run examples
    print("\n" + "="*80)
    print("Nexus Ray Framework - Complete Integration Example")
    print("="*80 + "\n")
    
    # Choose which example to run:
    # Option 1: Full integration (requires Kafka)
    # await run_protein_drug_workflow_integrated()
    
    # Option 2: Simple workflow (no external dependencies)
    await run_simple_workflow()


if __name__ == "__main__":
    asyncio.run(main())
