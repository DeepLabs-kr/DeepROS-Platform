import asyncio
import logging
from typing import Dict, Set, List, Optional, Callable
from ..models.topic import Topic
from ..models.message import Message
from ..models.subscription import Subscription
from ..config import settings

logger = logging.getLogger(__name__)


class TopicManager:
    """Manages MQTT topics, subscriptions, and message routing"""
    
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.wildcard_subscriptions: Dict[str, Set[str]] = {}  # pattern -> set of client_ids
        self.message_handlers: List[Callable[[Message], None]] = []
        
    def add_message_handler(self, handler: Callable[[Message], None]):
        """Add a message handler for processing messages"""
        self.message_handlers.append(handler)
    
    def remove_message_handler(self, handler: Callable[[Message], None]):
        """Remove a message handler"""
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)
    
    def get_or_create_topic(self, topic_name: str) -> Topic:
        """Get existing topic or create new one"""
        if topic_name not in self.topics:
            self.topics[topic_name] = Topic(name=topic_name)
            logger.debug(f"Created new topic: {topic_name}")
        return self.topics[topic_name]
    
    def subscribe(self, client_id: str, topic_pattern: str, qos: int = 0) -> bool:
        """Subscribe a client to a topic pattern"""
        try:
            # Handle wildcard subscriptions
            if self._is_wildcard_pattern(topic_pattern):
                if topic_pattern not in self.wildcard_subscriptions:
                    self.wildcard_subscriptions[topic_pattern] = set()
                self.wildcard_subscriptions[topic_pattern].add(client_id)
                logger.info(f"Client {client_id} subscribed to wildcard pattern: {topic_pattern}")
                return True
            
            # Handle exact topic subscription
            topic = self.get_or_create_topic(topic_pattern)
            topic.add_subscriber(client_id, qos)
            logger.info(f"Client {client_id} subscribed to topic: {topic_pattern} with QoS {qos}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing client {client_id} to {topic_pattern}: {e}")
            return False
    
    def unsubscribe(self, client_id: str, topic_pattern: str) -> bool:
        """Unsubscribe a client from a topic pattern"""
        try:
            # Handle wildcard subscriptions
            if topic_pattern in self.wildcard_subscriptions:
                self.wildcard_subscriptions[topic_pattern].discard(client_id)
                if not self.wildcard_subscriptions[topic_pattern]:
                    del self.wildcard_subscriptions[topic_pattern]
                logger.info(f"Client {client_id} unsubscribed from wildcard pattern: {topic_pattern}")
                return True
            
            # Handle exact topic subscription
            if topic_pattern in self.topics:
                self.topics[topic_pattern].remove_subscriber(client_id)
                logger.info(f"Client {client_id} unsubscribed from topic: {topic_pattern}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing client {client_id} from {topic_pattern}: {e}")
            return False
    
    def publish_message(self, message: Message) -> List[str]:
        """Publish a message to all matching subscribers"""
        subscribers = set()
        
        try:
            # Extract ROS info if enabled
            if settings.enable_ros_integration:
                message.extract_ros_info()
            
            # Find exact topic subscribers
            if message.topic in self.topics:
                topic = self.topics[message.topic]
                subscribers.update(topic.get_subscribers_list())
                
                # Handle retained messages
                if message.retain:
                    if message.payload:  # Set retained message
                        topic.set_retained_message(message)
                        logger.debug(f"Set retained message for topic: {message.topic}")
                    else:  # Clear retained message
                        topic.clear_retained_message()
                        logger.debug(f"Cleared retained message for topic: {message.topic}")
                else:
                    topic.increment_message_count()
            
            # Find wildcard subscribers
            for pattern, client_ids in self.wildcard_subscriptions.items():
                if self._topic_matches_pattern(message.topic, pattern):
                    subscribers.update(client_ids)
            
            # Call message handlers
            for handler in self.message_handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            
            logger.debug(f"Message published to {len(subscribers)} subscribers on topic: {message.topic}")
            return list(subscribers)
            
        except Exception as e:
            logger.error(f"Error publishing message to topic {message.topic}: {e}")
            return []
    
    def get_retained_message(self, topic_name: str) -> Optional[Message]:
        """Get retained message for a topic"""
        if topic_name in self.topics:
            return self.topics[topic_name].get_retained_message()
        return None
    
    def get_topic_info(self, topic_name: str) -> Optional[dict]:
        """Get information about a topic"""
        if topic_name in self.topics:
            return self.topics[topic_name].to_dict()
        return None
    
    def get_all_topics(self) -> List[dict]:
        """Get information about all topics"""
        return [topic.to_dict() for topic in self.topics.values()]
    
    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """Get all topics a client is subscribed to"""
        subscriptions = []
        
        # Check exact topic subscriptions
        for topic in self.topics.values():
            if client_id in topic.subscribers:
                subscriptions.append(topic.name)
        
        # Check wildcard subscriptions
        for pattern, client_ids in self.wildcard_subscriptions.items():
            if client_id in client_ids:
                subscriptions.append(pattern)
        
        return subscriptions
    
    def remove_client_subscriptions(self, client_id: str):
        """Remove all subscriptions for a client"""
        # Remove from exact topics
        for topic in self.topics.values():
            topic.remove_subscriber(client_id)
        
        # Remove from wildcard subscriptions
        for pattern in list(self.wildcard_subscriptions.keys()):
            self.wildcard_subscriptions[pattern].discard(client_id)
            if not self.wildcard_subscriptions[pattern]:
                del self.wildcard_subscriptions[pattern]
        
        logger.info(f"Removed all subscriptions for client: {client_id}")
    
    def _is_wildcard_pattern(self, pattern: str) -> bool:
        """Check if a topic pattern contains wildcards"""
        return '+' in pattern or '#' in pattern
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if a topic matches a wildcard pattern"""
        sub = Subscription(topic=pattern)
        return sub.matches_topic(topic)
    
    def cleanup_empty_topics(self):
        """Remove topics with no subscribers and no retained messages"""
        empty_topics = []
        for topic_name, topic in self.topics.items():
            if not topic.has_subscribers() and not topic.has_retained_message():
                empty_topics.append(topic_name)
        
        for topic_name in empty_topics:
            del self.topics[topic_name]
            logger.debug(f"Removed empty topic: {topic_name}")
    
    def get_statistics(self) -> dict:
        """Get broker statistics"""
        total_subscribers = sum(len(topic.subscribers) for topic in self.topics.values())
        total_retained_messages = sum(1 for topic in self.topics.values() if topic.has_retained_message())
        total_wildcard_subscriptions = sum(len(clients) for clients in self.wildcard_subscriptions.values())
        
        return {
            'total_topics': len(self.topics),
            'total_subscribers': total_subscribers + total_wildcard_subscriptions,
            'total_retained_messages': total_retained_messages,
            'wildcard_subscriptions': len(self.wildcard_subscriptions),
            'message_handlers': len(self.message_handlers),
        } 