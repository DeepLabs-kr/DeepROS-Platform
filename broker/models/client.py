from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from datetime import datetime
import asyncio


@dataclass
class Client:
    """Represents an MQTT client connection"""
    
    client_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    clean_session: bool = True
    keepalive: int = 60
    will_topic: Optional[str] = None
    will_message: Optional[str] = None
    will_qos: int = 0
    will_retain: bool = False
    
    # Connection state
    connected: bool = False
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    # Subscriptions
    subscriptions: Set[str] = field(default_factory=set)
    
    # Message handling
    inflight_messages: Dict[int, 'Message'] = field(default_factory=dict)
    queued_messages: list = field(default_factory=list)
    
    # Transport info
    transport: Optional[asyncio.Transport] = None
    protocol: Optional[asyncio.Protocol] = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_seen is None:
            self.last_seen = datetime.utcnow()
    
    def connect(self, transport: asyncio.Transport, protocol: asyncio.Protocol):
        """Mark client as connected"""
        self.connected = True
        self.connected_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.transport = transport
        self.protocol = protocol
    
    def disconnect(self):
        """Mark client as disconnected"""
        self.connected = False
        self.transport = None
        self.protocol = None
    
    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = datetime.utcnow()
    
    def add_subscription(self, topic: str, qos: int = 0):
        """Add a subscription"""
        self.subscriptions.add(topic)
    
    def remove_subscription(self, topic: str):
        """Remove a subscription"""
        self.subscriptions.discard(topic)
    
    def is_subscribed(self, topic: str) -> bool:
        """Check if client is subscribed to a topic"""
        return topic in self.subscriptions
    
    def add_inflight_message(self, message_id: int, message: 'Message'):
        """Add an inflight message"""
        self.inflight_messages[message_id] = message
    
    def remove_inflight_message(self, message_id: int):
        """Remove an inflight message"""
        self.inflight_messages.pop(message_id, None)
    
    def queue_message(self, message: 'Message'):
        """Queue a message for delivery"""
        self.queued_messages.append(message)
    
    def get_queued_message(self) -> Optional['Message']:
        """Get the next queued message"""
        return self.queued_messages.pop(0) if self.queued_messages else None
    
    def has_queued_messages(self) -> bool:
        """Check if client has queued messages"""
        return len(self.queued_messages) > 0
    
    def is_idle(self, timeout_seconds: int = 300) -> bool:
        """Check if client is idle (no activity for timeout_seconds)"""
        if not self.last_seen:
            return True
        return (datetime.utcnow() - self.last_seen).total_seconds() > timeout_seconds 