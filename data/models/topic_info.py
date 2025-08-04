from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Index
from sqlalchemy.sql import func
from ..database import Base
import json
from typing import Optional, Dict, Any


class TopicInfo(Base):
    """Model for storing ROS topic metadata and statistics."""
    
    __tablename__ = "topic_info"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Topic information
    topic_name = Column(String(255), nullable=False, unique=True, index=True)
    message_type = Column(String(255), nullable=False, index=True)
    
    # Statistics
    total_messages = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    first_seen = Column(Float, nullable=True)  # ROS time as float
    last_seen = Column(Float, nullable=True)  # ROS time as float
    
    # Frequency statistics
    avg_frequency_hz = Column(Float, default=0.0)
    max_frequency_hz = Column(Float, default=0.0)
    min_frequency_hz = Column(Float, default=0.0)
    
    # Size statistics
    avg_message_size = Column(Float, default=0.0)
    max_message_size = Column(Integer, default=0)
    min_message_size = Column(Integer, default=0)
    
    # Recording sessions
    sessions_count = Column(Integer, default=0)
    active_sessions = Column(Integer, default=0)
    
    # Metadata
    description = Column(Text, nullable=True)
    qos_profile = Column(Text, nullable=True)  # JSON string of default QoS settings
    publisher_nodes = Column(Text, nullable=True)  # JSON array of publisher node names
    subscriber_nodes = Column(Text, nullable=True)  # JSON array of subscriber node names
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_system_topic = Column(Boolean, default=False)  # e.g., /rosout, /clock
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_topic_active', 'is_active'),
        Index('idx_topic_message_type', 'message_type'),
        Index('idx_topic_frequency', 'avg_frequency_hz'),
        Index('idx_topic_size', 'avg_message_size'),
    )
    
    def __repr__(self):
        return f"<TopicInfo(topic='{self.topic_name}', type='{self.message_type}', messages={self.total_messages})>"
    
    @property
    def qos_dict(self) -> Optional[Dict[str, Any]]:
        """Get QoS profile as dictionary."""
        if self.qos_profile:
            try:
                return json.loads(self.qos_profile)
            except json.JSONDecodeError:
                return None
        return None
    
    @qos_dict.setter
    def qos_dict(self, value: Optional[Dict[str, Any]]):
        """Set QoS profile from dictionary."""
        if value is not None:
            self.qos_profile = json.dumps(value)
        else:
            self.qos_profile = None
    
    @property
    def publisher_list(self) -> list:
        """Get list of publisher nodes."""
        if self.publisher_nodes:
            try:
                return json.loads(self.publisher_nodes)
            except json.JSONDecodeError:
                return []
        return []
    
    @publisher_list.setter
    def publisher_list(self, value: list):
        """Set list of publisher nodes."""
        if value is not None:
            self.publisher_nodes = json.dumps(value)
        else:
            self.publisher_nodes = None
    
    @property
    def subscriber_list(self) -> list:
        """Get list of subscriber nodes."""
        if self.subscriber_nodes:
            try:
                return json.loads(self.subscriber_nodes)
            except json.JSONDecodeError:
                return []
        return []
    
    @subscriber_list.setter
    def subscriber_list(self, value: list):
        """Set list of subscriber nodes."""
        if value is not None:
            self.subscriber_nodes = json.dumps(value)
        else:
            self.subscriber_nodes = None
    
    def update_statistics(self, messages_data: list):
        """Update topic statistics from message data."""
        if not messages_data:
            return
        
        # Basic counts
        self.total_messages = len(messages_data)
        self.total_size_bytes = sum(msg.get('data_size', 0) for msg in messages_data)
        
        # Timing
        timestamps = [msg.get('timestamp', 0) for msg in messages_data if msg.get('timestamp')]
        if timestamps:
            self.first_seen = min(timestamps)
            self.last_seen = max(timestamps)
        
        # Size statistics
        sizes = [msg.get('data_size', 0) for msg in messages_data if msg.get('data_size')]
        if sizes:
            self.avg_message_size = sum(sizes) / len(sizes)
            self.max_message_size = max(sizes)
            self.min_message_size = min(sizes)
        
        # Frequency calculation (simplified)
        if len(timestamps) > 1:
            time_span = self.last_seen - self.first_seen
            if time_span > 0:
                self.avg_frequency_hz = len(timestamps) / time_span 