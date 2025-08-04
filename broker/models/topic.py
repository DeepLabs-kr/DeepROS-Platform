from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List
from datetime import datetime
from .message import Message
from .subscription import Subscription


@dataclass
class Topic:
    """Represents an MQTT topic"""
    
    name: str
    retained_message: Optional[Message] = None
    subscribers: Set[str] = field(default_factory=set)  # Set of client IDs
    subscription_qos: Dict[str, int] = field(default_factory=dict)  # client_id -> qos
    
    # Statistics
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def add_subscriber(self, client_id: str, qos: int = 0):
        """Add a subscriber to this topic"""
        self.subscribers.add(client_id)
        self.subscription_qos[client_id] = qos
    
    def remove_subscriber(self, client_id: str):
        """Remove a subscriber from this topic"""
        self.subscribers.discard(client_id)
        self.subscription_qos.pop(client_id, None)
    
    def has_subscribers(self) -> bool:
        """Check if topic has any subscribers"""
        return len(self.subscribers) > 0
    
    def get_subscriber_qos(self, client_id: str) -> int:
        """Get QoS level for a specific subscriber"""
        return self.subscription_qos.get(client_id, 0)
    
    def set_retained_message(self, message: Message):
        """Set the retained message for this topic"""
        self.retained_message = message
    
    def get_retained_message(self) -> Optional[Message]:
        """Get the retained message for this topic"""
        return self.retained_message
    
    def clear_retained_message(self):
        """Clear the retained message"""
        self.retained_message = None
    
    def has_retained_message(self) -> bool:
        """Check if topic has a retained message"""
        return self.retained_message is not None
    
    def increment_message_count(self):
        """Increment message counter"""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()
    
    def get_subscribers_list(self) -> List[str]:
        """Get list of subscriber client IDs"""
        return list(self.subscribers)
    
    def to_dict(self) -> dict:
        """Convert topic to dictionary"""
        return {
            'name': self.name,
            'retained_message': self.retained_message.to_dict() if self.retained_message else None,
            'subscribers': list(self.subscribers),
            'subscription_qos': self.subscription_qos,
            'message_count': self.message_count,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        """Create topic from dictionary"""
        # Parse timestamps
        last_message_at = None
        created_at = None
        
        if data.get('last_message_at'):
            try:
                last_message_at = datetime.fromisoformat(data['last_message_at'])
            except ValueError:
                pass
        
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass
        
        # Parse retained message
        retained_message = None
        if data.get('retained_message'):
            retained_message = Message.from_dict(data['retained_message'])
        
        # Create topic
        topic = cls(
            name=data['name'],
            retained_message=retained_message,
            message_count=data.get('message_count', 0),
            last_message_at=last_message_at,
            created_at=created_at,
        )
        
        # Add subscribers
        for client_id in data.get('subscribers', []):
            qos = data.get('subscription_qos', {}).get(client_id, 0)
            topic.add_subscriber(client_id, qos)
        
        return topic 