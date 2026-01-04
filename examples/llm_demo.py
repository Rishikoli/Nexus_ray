"""
LLM demonstration with OpenVINO optimization.

Shows text generation, chat completion, and JSON mode.
"""

import asyncio
from loguru import logger

from src.llm import get_llm, PromptBuilder, PromptTemplate, parse_llm_output


def demo_text_generation():
    """Demonstrate basic text generation"""
    print("=" * 80)
    print("LLM Demo - Text Generation")
    print("=" * 80)
    print()
    
    # Get LLM instance (uses Mistral-7B by default)
    logger.info("Loading LLM...")
    llm = get_llm("mistral-7b-ov")
    logger.info(f"✅ Loaded: {llm}")
    print()
    
    # Simple generation
    prompt = "Explain what vector databases are in 2-3 sentences:"
    
    logger.info(f"Prompt: {prompt}")
    response = llm.generate(prompt, max_tokens=150, temperature=0.7)
    
    print(f"Response:\n{response}")
    print()
    
    # Show stats
    stats = llm.get_stats()
    logger.info(f"Model stats: {stats}")
    print()


def demo_chat_completion():
    """Demonstrate chat completion"""
    print("=" * 80)
    print("LLM Demo - Chat Completion")
    print("=" * 80)
    print()
    
    llm = get_llm("mistral-7b-ov")
    
    # Chat messages
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant specialized in software development."},
        {"role": "user", "content": "What are the benefits of using OpenVINO for LLM inference?"}
    ]
    
    logger.info("Sending chat messages...")
    response = llm.chat(messages, max_tokens=200)
    
    print(f"Assistant:\n{response}")
    print()


def demo_prompt_templates():
    """Demonstrate prompt templates"""
    print("=" * 80)
    print("LLM Demo - Prompt Templates")
    print("=" * 80)
    print()
    
    llm = get_llm("mistral-7b-ov")
    
    # Using analysis template
    builder = PromptBuilder(PromptTemplate.ANALYSIS)
    builder.set("context", "Python is a high-level programming language")
    builder.set("query", "Why is Python popular for data science?")
    
    prompt = builder.build()
    
    logger.info("Using ANALYSIS template...")
    response = llm.generate(prompt, max_tokens=250)
    
    print(f"Analysis:\n{response}")
    print()


def demo_json_mode():
    """Demonstrate JSON output mode"""
    print("=" * 80)
    print("LLM Demo - JSON Mode")
    print("=" * 80)
    print()
    
    llm = get_llm("mistral-7b-ov")
    
    # JSON mode prompt
    builder = PromptBuilder(PromptTemplate.JSON_MODE)
    builder.set("task", "Extract key information from the text")
    builder.set("input_data", "John Smith is a 35-year-old software engineer living in San Francisco. He specializes in machine learning.")
    builder.set("schema", '{"name": "string", "age": "number", "occupation": "string", "city": "string", "specialty": "string"}')
    
    prompt = builder.build()
    
    logger.info("Requesting JSON output...")
    response = llm.generate(prompt, max_tokens=150, temperature=0.3)
    
    print(f"Raw response:\n{response}\n")
    
    # Parse JSON
    parsed = parse_llm_output(response, output_type="json")
    
    if parsed:
        print("Parsed JSON:")
        for key, value in parsed.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to parse JSON")
    
    print()


def demo_with_workflow():
    """Demonstrate LLM in workflow"""
    print("=" * 80)
    print("LLM Demo - Workflow Integration")
    print("=" * 80)
    print()
    
    from src.sdk import WorkflowBuilder
    from src.core.orchestrator import WorkflowOrchestrator
    
    # Build workflow with LLM task
    workflow = (
        WorkflowBuilder("llm_demo_workflow")
        .add_llm_task(
            task_id="analyze",
            name="Analysis Task",
            description="Analyze the benefits of OpenVINO",
            inputs={"topic": "OpenVINO for AI"},
            metadata={"output_type": "text", "max_tokens": 200}
        )
        .compile()
    )
    
    logger.info(f"Created workflow: {workflow.workflow_id}")
    
    # Execute
    async def run_workflow():
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Show results
        for task_id, result in state.task_results.items():
            if result.outputs:
                print(f"\nTask {task_id} result:")
                print(result.outputs.get("result", result.outputs))
    
    logger.info("Executing workflow...")
    asyncio.run(run_workflow())
    print()


def main():
    """Run all demos"""
    try:
        demo_text_generation()
        demo_chat_completion()
        demo_prompt_templates()
        demo_json_mode()
        demo_with_workflow()
        
        logger.info("✅ All LLM demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
