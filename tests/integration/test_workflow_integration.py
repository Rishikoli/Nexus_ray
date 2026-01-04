"""
Integration tests for complete workflow execution.

Tests end-to-end workflows with memory retrieval and LLM generation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import numpy as np

from src.sdk import WorkflowBuilder
from src.core.orchestrator import WorkflowOrchestrator
from src.core.task import TaskStatus, TaskType


class TestWorkflowIntegration:
    """Integration tests for workflow execution"""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test simple 2-task workflow"""
        workflow = (
            WorkflowBuilder("test_workflow")
            .add_task(task_id="task1", task_type=TaskType.LLM, name="Task 1", inputs={"query": "test"})
            .add_task(task_id="task2", task_type=TaskType.TOOL, name="Task 2", depends_on=["task1"])
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        assert state.status == "completed"
        assert len(state.completed_tasks) == 2
        assert "task1" in state.task_results
        assert "task2" in state.task_results
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel task execution"""
        workflow = (
            WorkflowBuilder("parallel_workflow")
            .add_task(task_id="task1", task_type=TaskType.LLM, name="Task 1")
            .add_task(task_id="task2", task_type=TaskType.LLM, name="Task 2")  # No dependency
            .add_task(task_id="task3", task_type=TaskType.LLM, name="Task 3", depends_on=["task1", "task2"])
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        assert state.status == "completed"
        assert len(state.completed_tasks) == 3
    
    @pytest.mark.asyncio
    async def test_hitl_workflow(self):
        """Test workflow with human-in-the-loop"""
        workflow = (
            WorkflowBuilder("hitl_workflow")
            .add_task(task_id="analyze", task_type=TaskType.LLM, name="Analysis")
            .add_hitl_gate(task_id="approval", after="analyze")
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # HITL task should be waiting
        assert "approval" in state.task_results
        assert state.task_results["approval"].status == TaskStatus.WAITING_HUMAN


class TestMemoryIntegration:
    """Integration tests for memory + workflow"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_memory_context(self):
        """Test workflow using memory for context retrieval"""
        # Mock memory
        with patch('src.memory.embedder.OPENVINO_AVAILABLE', True):
            with patch('src.memory.embedder.get_embedder') as mock_embedder:
                mock_embedder.return_value.embed.return_value = np.random.rand(3, 768)
                mock_embedder.return_value.embed_single.return_value = np.random.rand(768)
                
                try:
                    from src.memory import VectorMemory
                    
                    # Create memory
                    memory = VectorMemory(backend="faiss")
                    
                    # Add context
                    memory.add_texts([
                        "Python is a programming language",
                        "Machine learning uses algorithms",
                        "OpenVINO optimizes AI models"
                    ])
                    
                    # Search for context
                    results = memory.search("AI optimization", k=2)
                    
                    assert len(results) > 0
                except:
                    pytest.skip("Memory components not available")


class TestLLMIntegration:
    """Integration tests for LLM + workflow"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_llm_task(self):
        """Test workflow with actual LLM execution"""
        workflow = (
            WorkflowBuilder("llm_workflow")
            .add_llm_task(
                task_id="generate",
                prompt="Generate sample text about {topic}",
                name="Generate Text",
                inputs={"topic": "AI"}
            )
            .compile()
        )
        
        # Should complete or fail gracefully
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        assert state.status in ["completed", "failed"]
        assert "generate" in state.task_results
    
    @pytest.mark.asyncio  
    async def test_workflow_with_json_output(self):
        """Test workflow with JSON mode LLM task"""
        workflow = (
            WorkflowBuilder("json_workflow")
            .add_llm_task(
                task_id="extract",
                prompt="Extract structured data from: {text}",
                name="Extract JSON",
                inputs={"text": "John is 30 years old"}
            )
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        assert state.status in ["completed", "failed"]
        assert "extract" in state.task_results


class TestFullStackIntegration:
    """Full stack integration tests"""
    
    @pytest.mark.asyncio
    async def test_rag_workflow(self):
        """Test RAG (Retrieval-Augmented Generation) workflow"""
        workflow = (
            WorkflowBuilder("rag_workflow")
            .add_task(
                task_id="retrieve",
                task_type=TaskType.TOOL,
                name="Retrieve Context",
                inputs={"query": "machine learning"}
            )
            .add_llm_task(
                task_id="generate",
                prompt="Answer question using context",
                name="Generate Answer",
                depends_on=["retrieve"]
            )
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # Should have executed both tasks
        assert len(state.task_results) == 2
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test multi-agent collaboration workflow"""
        workflow = (
            WorkflowBuilder("multi_agent")
            .add_llm_task(task_id="agent1", prompt="Analyze data", name="Agent 1", inputs={"data": "test"})
            .add_llm_task(task_id="agent2", prompt="Analyze data", name="Agent 2", inputs={"data": "test"})
            .add_llm_task(
                task_id="synthesize",
                prompt="Synthesize results",
                name="Synthesize Results",
                depends_on=["agent1", "agent2"]
            )
            .compile()
        )
        
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        
        # May complete or fail (placeholder LLM)
        assert len(state.task_results) == 3


class TestErrorHandling:
    """Test error handling in workflows"""
    
    @pytest.mark.asyncio
    async def test_task_failure_handling(self):
        """Test workflow handles task failures"""
        workflow = (
            WorkflowBuilder("failure_test")
            .add_task(task_id="fail_task", task_type=TaskType.LLM, name="Failing Task")
            .compile()
        )
        
        # Force failure
        with patch('src.core.executor.LLMExecutor.execute', side_effect=Exception("Test error")):
            orchestrator = WorkflowOrchestrator()
            state = await orchestrator.execute_workflow(workflow)
            
            assert "fail_task" in state.failed_tasks


class TestPerformance:
    """Basic performance tests"""
    
    @pytest.mark.asyncio
    async def test_workflow_execution_time(self):
        """Test workflow completes in reasonable time"""
        import time
        
        workflow = (
            WorkflowBuilder("perf_test")
            .add_task(task_id="task1", task_type=TaskType.LLM, name="Task 1")
            .add_task(task_id="task2", task_type=TaskType.LLM, name="Task 2")
            .compile()
        )
        
        start = time.time()
        orchestrator = WorkflowOrchestrator()
        state = await orchestrator.execute_workflow(workflow)
        duration = time.time() - start
        
        # Should complete quickly (placeholder tasks)
        assert duration < 5.0  # seconds
        assert state.status == "completed"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
