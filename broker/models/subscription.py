from dataclasses import dataclass
from typing import Set, Optional
from datetime import datetime


@dataclass
class Subscription:
    """Represents an MQTT topic subscription"""
    
    topic: str
    qos: int = 0
    client_id: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def matches_topic(self, message_topic: str) -> bool:
        """Check if this subscription matches a message topic"""
        return self._topic_matches(self.topic, message_topic)
    
    def _topic_matches(self, subscription: str, message_topic: str) -> bool:
        """Check if subscription pattern matches message topic"""
        sub_parts = subscription.split('/')
        msg_parts = message_topic.split('/')
        
        # Handle exact match
        if subscription == message_topic:
            return True
        
        # Handle wildcards
        if subscription == '#':
            return True
        
        if subscription.endswith('/#'):
            prefix = subscription[:-2]  # Remove '/#'
            return message_topic.startswith(prefix)
        
        # Handle + wildcard
        if len(sub_parts) != len(msg_parts):
            return False
        
        for sub_part, msg_part in zip(sub_parts, msg_parts):
            if sub_part == '+':
                continue
            if sub_part != msg_part:
                return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert subscription to dictionary"""
        return {
            'topic': self.topic,
            'qos': self.qos,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Subscription':
        """Create subscription from dictionary"""
        timestamp = None
        if data.get('timestamp'):
            try:
                timestamp = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pass
        
        return cls(
            topic=data['topic'],
            qos=data.get('qos', 0),
            client_id=data.get('client_id', ''),
            timestamp=timestamp,
        ) 