"""
Kafka client wrapper for producer and consumer operations.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from loguru import logger


class KafkaConfig:
    """Kafka configuration"""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "nexus-ray",
        group_id: str = "nexus-ray-group"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.group_id = group_id


class KafkaProducer:
    """
    Async Kafka producer for publishing messages.
    
    Handles message serialization and error handling.
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        self.config = config or KafkaConfig()
        self.producer: Optional[AIOKafkaProducer] = None
        logger.info(f"KafkaProducer initialized: {self.config.bootstrap_servers}")
    
    async def start(self) -> None:
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=self.config.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type="gzip"
            )
            await self.producer.start()
            logger.info("KafkaProducer started successfully")
        except KafkaError as e:
            logger.error(f"Failed to start KafkaProducer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("KafkaProducer stopped")
    
    async def send(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """
        Send a message to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            message: Message payload (will be JSON serialized)
            key: Optional message key for partitioning
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()
            
            key_bytes = key.encode('utf-8') if key else None
            
            # Send message
            await self.producer.send(topic, value=message, key=key_bytes)
            
            logger.debug(f"Sent message to {topic}: {message.get('type', 'message')}")
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise
    
    async def send_batch(
        self,
        topic: str,
        messages: List[Dict[str, Any]]
    ) -> None:
        """Send multiple messages in batch"""
        for message in messages:
            await self.send(topic, message)


class KafkaConsumer:
    """
    Async Kafka consumer for subscribing to topics.
    
    Supports message deserialization and automatic callback handling.
    """
    
    def __init__(
        self,
        topics: List[str],
        config: Optional[KafkaConfig] = None,
        callback: Optional[Callable] = None
    ):
        self.config = config or KafkaConfig()
        self.topics = topics
        self.callback = callback
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        
        logger.info(f"KafkaConsumer initialized for topics: {topics}")
    
    async def start(self) -> None:
        """Start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=self.config.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            await self.consumer.start()
            logger.info(f"KafkaConsumer started for topics: {self.topics}")
        except KafkaError as e:
            logger.error(f"Failed to start KafkaConsumer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer"""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("KafkaConsumer stopped")
    
    async def consume(self) -> None:
        """
        Start consuming messages and invoke callback.
        
        This is a long-running task that should be run in the background.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")
        
        self._running = True
        logger.info("Starting message consumption loop")
        
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                
                try:
                    topic = msg.topic
                    value = msg.value
                    
                    logger.debug(f"Received message from {topic}")
                    
                    # Invoke callback if provided
                    if self.callback:
                        if asyncio.iscoroutinefunction(self.callback):
                            await self.callback(topic, value)
                        else:
                            self.callback(topic, value)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages
        
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise
    
    async def get_messages(self, max_messages: int = 10, timeout: float = 1.0) -> List[Dict]:
        """
        Get a batch of messages (for testing/debugging).
        
        Args:
            max_messages: Maximum number of messages to retrieve
            timeout: Timeout in seconds
            
        Returns:
            List of messages
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started")
        
        messages = []
        try:
            async with asyncio.timeout(timeout):
                async for msg in self.consumer:
                    messages.append(msg.value)
                    if len(messages) >= max_messages:
                        break
        except asyncio.TimeoutError:
            pass
        
        return messages


class KafkaClient:
    """
    High-level Kafka client combining producer and consumer.
    
    Provides a unified interface for Kafka operations.
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        self.config = config or KafkaConfig()
        self.producer = KafkaProducer(self.config)
        self.consumers: Dict[str, KafkaConsumer] = {}
        
        logger.info("KafkaClient initialized")
    
    async def start(self) -> None:
        """Start producer and all consumers"""
        await self.producer.start()
        
        for consumer in self.consumers.values():
            await consumer.start()
        
        logger.info("KafkaClient started")
    
    async def stop(self) -> None:
        """Stop producer and all consumers"""
        await self.producer.stop()
        
        for consumer in self.consumers.values():
            await consumer.stop()
        
        logger.info("KafkaClient stopped")
    
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """Publish a message to a topic"""
        await self.producer.send(topic, message, key)
    
    def subscribe(
        self,
        topics: List[str],
        callback: Callable,
        consumer_id: Optional[str] = None
    ) -> KafkaConsumer:
        """
        Subscribe to topics with a callback.
        
        Args:
            topics: List of topics to subscribe to
            callback: Async function to call for each message
            consumer_id: Optional consumer identifier
            
        Returns:
            KafkaConsumer instance
        """
        consumer_id = consumer_id or f"consumer_{len(self.consumers)}"
        
        consumer = KafkaConsumer(topics, self.config, callback)
        self.consumers[consumer_id] = consumer
        
        logger.info(f"Subscribed to {topics} with consumer {consumer_id}")
        
        return consumer
    
    async def __aenter__(self):
        """Context manager support"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        await self.stop()
