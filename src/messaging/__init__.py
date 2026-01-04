"""Messaging components"""

from src.messaging.kafka_client import (
    KafkaConfig,
    KafkaProducer,
    KafkaConsumer,
    KafkaClient
)
from src.messaging.message_router import (
    MessageRouter,
    TopicType,
    MessageType
)
from src.messaging.subscriptions import (
    subscribe,
    SubscriptionManager,
    get_subscriptions,
    clear_subscriptions
)

# Singleton for message router
_message_router = None

def get_message_router():
    """Get or create singleton MessageRouter instance"""
    global _message_router
    if _message_router is None:
        _message_router = MessageRouter()
    return _message_router

__all__ = [
    "KafkaConfig",
    "KafkaProducer",
    "KafkaConsumer",
    "KafkaClient",
    "MessageRouter",
    "get_message_router",
    "TopicType",
    "MessageType",
    "subscribe",
    "SubscriptionManager",
    "get_subscriptions",
    "clear_subscriptions",
]
