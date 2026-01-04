"""
Decorator-based subscription system for Kafka topics.

Allows agents to subscribe to topics using decorators.
"""

import functools
from typing import Callable, List, Optional, Dict, Any
from loguru import logger


# Global registry of subscriptions
_SUBSCRIPTIONS: Dict[str, List[Callable]] = {}


def subscribe(topic: str, consumer_id: Optional[str] = None):
    """
    Decorator to subscribe a function to a Kafka topic.
    
    Usage:
        @subscribe(topic="agent.inbox.my_agent")
        async def on_message(topic: str, message: dict):
            print(f"Received: {message}")
    
    Args:
        topic: Kafka topic to subscribe to
        consumer_id: Optional consumer identifier
    """
    def decorator(func: Callable):
        # Register the subscription
        if topic not in _SUBSCRIPTIONS:
            _SUBSCRIPTIONS[topic] = []
        
        _SUBSCRIPTIONS[topic].append(func)
        
        logger.debug(f"Registered subscription: {func.__name__} -> {topic}")
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Attach metadata
        wrapper._kafka_topic = topic
        wrapper._consumer_id = consumer_id
        
        return wrapper
    
    return decorator


def get_subscriptions() -> Dict[str, List[Callable]]:
    """Get all registered subscriptions"""
    return _SUBSCRIPTIONS.copy()


def clear_subscriptions() -> None:
    """Clear all subscriptions (for testing)"""
    global _SUBSCRIPTIONS
    _SUBSCRIPTIONS = {}


class SubscriptionManager:
    """
    Manages subscription lifecycle for agents.
    
    Automatically starts consumers for decorated functions.
    """
    
    def __init__(self, kafka_client):
        self.kafka_client = kafka_client
        self.active_consumers = []
        logger.info("SubscriptionManager initialized")
    
    async def start_all_subscriptions(self) -> None:
        """
        Start consumers for all registered subscriptions.
        """
        subscriptions = get_subscriptions()
        
        logger.info(f"Starting {len(subscriptions)} subscriptions")
        
        for topic, callbacks in subscriptions.items():
            # Create combined callback for all functions on this topic
            async def topic_callback(t: str, message: Dict[str, Any]):
                for callback in callbacks:
                    try:
                        await callback(t, message)
                    except Exception as e:
                        logger.error(
                            f"Error in subscription callback {callback.__name__}: {e}",
                            exc_info=True
                        )
            
            # Subscribe to topic
            consumer = self.kafka_client.subscribe(
                topics=[topic],
                callback=topic_callback,
                consumer_id=f"subscription_{topic}"
            )
            
            await consumer.start()
            self.active_consumers.append(consumer)
            
            # Start consumption loop in background
            import asyncio
            asyncio.create_task(consumer.consume())
        
        logger.info(f"Started {len(self.active_consumers)} consumers")
    
    async def stop_all_subscriptions(self) -> None:
        """Stop all active consumers"""
        for consumer in self.active_consumers:
            await consumer.stop()
        
        self.active_consumers = []
        logger.info("Stopped all subscriptions")


# Example usage for reference agents

class ExampleProteinDrugAgent:
    """Example showing how agents use subscriptions"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    @subscribe(topic="agent.inbox.structure_predictor")
    async def on_structure_request(self, topic: str, message: dict):
        """Handle structure prediction requests"""
        logger.info(f"Structure prediction requested: {message}")
        
        # Process message
        sequence = message.get('sequence')
        # ... prediction logic ...
        
        # Could publish response to another topic
        # await kafka_client.publish(...)
    
    @subscribe(topic="workflow.events")
    async def on_workflow_event(self, topic: str, message: dict):
        """Listen to all workflow events"""
        event_type = message.get('type')
        
        if event_type == "task_completed":
            logger.info(f"Task completed: {message.get('task_id')}")


class ExampleSemiconductorAgent:
    """Example for semiconductor agent"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    @subscribe(topic="agent.inbox.defect_detector")
    async def on_defect_detection_request(self, topic: str, message: dict):
        """Handle defect detection requests"""
        logger.info(f"Defect detection requested: {message}")
        
        wafer_image = message.get('wafer_image')
        # ... detection logic ...
    
    @subscribe(topic="agent.broadcast")
    async def on_broadcast(self, topic: str, message: dict):
        """Listen to broadcast messages"""
        logger.debug(f"Broadcast received: {message.get('type')}")
