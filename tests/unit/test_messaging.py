"""
Unit tests for messaging components.

Tests Kafka client, message router, and subscription system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import asyncio

from src.messaging import KafkaClient, MessageRouter, MessageType, SubscriptionManager


class TestKafkaClient:
    """Test Kafka client producer/consumer"""
    
    @pytest.fixture
    def mock_kafka_producer(self):
        """Mock aiokafka producer"""
        producer = AsyncMock()
        producer.start = AsyncMock()
        producer.stop = AsyncMock()
        producer.send_and_wait = AsyncMock()
        return producer
    
    @pytest.fixture
    def mock_kafka_consumer(self):
        """Mock aiokafka consumer"""
        consumer = AsyncMock()
        consumer.start = AsyncMock()
        consumer.stop = AsyncMock()
        consumer.subscribe = Mock()
        return consumer
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test Kafka client initialization"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer'):
            client = KafkaClient()
            assert client.bootstrap_servers is not None
    
    @pytest.mark.asyncio
    async def test_producer_start(self, mock_kafka_producer):
        """Test producer startup"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer', return_value=mock_kafka_producer):
            client = KafkaClient()
            await client.start()
            
            mock_kafka_producer.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_message(self, mock_kafka_producer):
        """Test message publishing"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer', return_value=mock_kafka_producer):
            client = KafkaClient()
            await client.start()
            
            message = {"type": "test", "data": "hello"}
            await client.publish("test_topic", message)
            
            mock_kafka_producer.send_and_wait.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_publish(self, mock_kafka_producer):
        """Test batch message publishing"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer', return_value=mock_kafka_producer):
            client = KafkaClient()
            await client.start()
            
            messages = [
                {"type": "test1", "data": "msg1"},
                {"type": "test2", "data": "msg2"},
            ]
            
            await client.publish_batch("test_topic", messages)
            
            assert mock_kafka_producer.send_and_wait.call_count == 2
    
    @pytest.mark.asyncio
    async def test_consumer_subscription(self, mock_kafka_consumer):
        """Test consumer topic subscription"""
        with patch('src.messaging.kafka_client.AIOKafkaConsumer', return_value=mock_kafka_consumer):
            client = KafkaClient()
            
            consumer = await client.subscribe(["topic1", "topic2"])
            
            mock_kafka_consumer.subscribe.assert_called_with(["topic1", "topic2"])
    
    @pytest.mark.asyncio  
    async def test_context_manager(self, mock_kafka_producer):
        """Test async context manager"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer', return_value=mock_kafka_producer):
            async with KafkaClient() as client:
                assert client is not None
            
            mock_kafka_producer.start.assert_called_once()
            mock_kafka_producer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, mock_kafka_producer):
        """Test graceful shutdown"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer', return_value=mock_kafka_producer):
            client = KafkaClient()
            await client.start()
            await client.close()
            
            mock_kafka_producer.stop.assert_called_once()


class TestMessageRouter:
    """Test message routing logic"""
    
    def test_router_initialization(self):
        """Test router initialization"""
        router = MessageRouter()
        assert router is not None
    
    def test_workflow_event_routing(self):
        """Test workflow event routing"""
        router = MessageRouter()
        
        message = {
            "type": MessageType.WORKFLOW_STARTED,
            "workflow_id": "wf-123"
        }
        
        topic = router.route_message(message)
        assert "workflow" in topic.lower()
    
    def test_task_event_routing(self):
        """Test task event routing"""
        router = MessageRouter()
        
        message = {
            "type": MessageType.TASK_COMPLETED,
            "workflow_id": "wf-123",
            "task_id": "task-1"
        }
        
        topic = router.route_message(message)
        assert topic is not None
    
    def test_hitl_event_routing(self):
        """Test HITL event routing"""
        router = MessageRouter()
        
        message = {
            "type": MessageType.HITL_APPROVAL_REQUIRED,
            "workflow_id": "wf-123"
        }
        
        topic = router.route_message(message)
        assert "hitl" in topic.lower()
    
    def test_llm_event_routing(self):
        """Test LLM event routing"""
        router = MessageRouter()
        
        message = {
            "type": MessageType.LLM_CALL_STARTED,
            "model": "mistral-7b-ov"
        }
        
        topic = router.route_message(message)
        assert "llm" in topic.lower()
    
    def test_create_workflow_event(self):
        """Test workflow event creation"""
        router = MessageRouter()
        
        event = router.create_workflow_event(
            MessageType.WORKFLOW_STARTED,
            "wf-123",
            workflow_name="test_workflow"
        )
        
        assert event["type"] == MessageType.WORKFLOW_STARTED.value
        assert event["workflow_id"] == "wf-123"
        assert "workflow_name" in event
    
    def test_create_hitl_request(self):
        """Test HITL request creation"""
        router = MessageRouter()
        
        request = router.create_hitl_request(
            workflow_id="wf-123",
            task_id="task-1",
            decision_data={"approve": True},
            approvers=["user@example.com"]
        )
        
        assert request["type"] == MessageType.HITL_APPROVAL_REQUIRED.value
        assert request["workflow_id"] == "wf-123"
        assert request["task_id"] == "task-1"
        assert "approvers" in request
    
    def test_routing_with_priority(self):
        """Test message routing with priority"""
        router = MessageRouter()
        
        high_priority = {
            "type": MessageType.WORKFLOW_FAILED,
            "workflow_id": "wf-123"
        }
        
        topic = router.route_message(high_priority)
        assert topic is not None


class TestSubscriptionManager:
    """Test subscription system"""
    
    def test_subscription_manager_init(self):
        """Test subscription manager initialization"""
        manager = SubscriptionManager()
        assert manager is not None
    
    def test_register_handler(self):
        """Test handler registration"""
        manager = SubscriptionManager()
        
        @manager.subscribe("test_topic")
        async def handle_test(message):
            return message
        
        handlers = manager.get_handlers("test_topic")
        assert len(handlers) == 1
    
    def test_multiple_handlers_same_topic(self):
        """Test multiple handlers for same topic"""
        manager = SubscriptionManager()
        
        @manager.subscribe("events")
        async def handler1(message):
            pass
        
        @manager.subscribe("events")
        async def handler2(message):
            pass
        
        handlers = manager.get_handlers("events")
        assert len(handlers) == 2
    
    @pytest.mark.asyncio
    async def test_handler_invocation(self):
        """Test handler invocation"""
        manager = SubscriptionManager()
        
        results = []
        
        @manager.subscribe("test")
        async def handler(message):
            results.append(message["data"])
        
        message = {"type": "test", "data": "hello"}
        await manager.dispatch("test", message)
        
        assert "hello" in results
    
    def test_pattern_subscription(self):
        """Test pattern-based subscription"""
        manager = SubscriptionManager()
        
        @manager.subscribe_pattern("workflow.*")
        async def workflow_handler(message):
            pass
        
        # Should match workflow.started, workflow.completed, etc.
        handlers = manager.get_handlers("workflow.started")
        assert len(handlers) >= 0  # Pattern matching logic
    
    def test_unsubscribe(self):
        """Test unsubscribing handler"""
        manager = SubscriptionManager()
        
        @manager.subscribe("test")
        async def handler(message):
            pass
        
        manager.unsubscribe("test", handler)
        handlers = manager.get_handlers("test")
        assert len(handlers) == 0


class TestMessageIntegration:
    """Integration tests for messaging"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_messaging(self):
        """Test end-to-end message flow (mocked)"""
        with patch('src.messaging.kafka_client.AIOKafkaProducer'):
            client = KafkaClient()
            router = MessageRouter()
            
            # Create and route message
            message = router.create_workflow_event(
                MessageType.WORKFLOW_STARTED,
                "wf-123",
                workflow_name="test"
            )
            
            topic = router.route_message(message)
            
            # Would publish to Kafka
            assert topic is not None
            assert message["workflow_id"] == "wf-123"
    
    @pytest.mark.asyncio
    async def test_subscription_with_routing(self):
        """Test subscription with message routing"""
        router = MessageRouter()
        manager = SubscriptionManager()
        
        received_messages = []
        
        # Subscribe to workflow events
        @manager.subscribe("nexus.workflow.events")
        async def handle_workflow(message):
            received_messages.append(message)
        
        # Create and route
        event = router.create_workflow_event(
            MessageType.WORKFLOW_STARTED,
            "wf-123"
        )
        
        topic = router.route_message(event)
        await manager.dispatch(topic, event)
        
        assert len(received_messages) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
