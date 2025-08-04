from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import json
from typing import Optional, Dict, Any


class RecordingSession(Base):
    """Model for managing recording sessions."""
    
    __tablename__ = "recording_sessions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Session metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timing information
    start_time = Column(Float, nullable=False, index=True)  # ROS time as float
    end_time = Column(Float, nullable=True, index=True)  # ROS time as float
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Session state
    is_active = Column(Boolean, default=True, index=True)
    is_compressed = Column(Boolean, default=False)
    
    # Statistics
    total_messages = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    topics_count = Column(Integer, default=0)
    
    # Configuration
    settings = Column(Text, nullable=True)  # JSON string of recording settings
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("ROSMessage", back_populates="recording_session", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_active', 'is_active'),
        Index('idx_session_time_range', 'start_time', 'end_time'),
        Index('idx_session_name', 'name'),
    )
    
    def __repr__(self):
        return f"<RecordingSession(id={self.id}, name='{self.name}', active={self.is_active}, messages={self.total_messages})>"
    
    @property
    def settings_dict(self) -> Optional[Dict[str, Any]]:
        """Get recording settings as dictionary."""
        if self.settings:
            try:
                return json.loads(self.settings)
            except json.JSONDecodeError:
                return None
        return None
    
    @settings_dict.setter
    def settings_dict(self, value: Optional[Dict[str, Any]]):
        """Set recording settings from dictionary."""
        if value is not None:
            self.settings = json.dumps(value)
        else:
            self.settings = None
    
    def update_statistics(self):
        """Update session statistics from related messages."""
        if self.messages:
            self.total_messages = len(self.messages)
            self.total_size_bytes = sum(msg.data_size for msg in self.messages)
            self.topics_count = len(set(msg.topic_name for msg in self.messages))
            
            if self.messages:
                self.start_time = min(msg.timestamp for msg in self.messages)
                self.end_time = max(msg.timestamp for msg in self.messages)
                self.duration = self.end_time - self.start_time
    
    def get_topic_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each topic in this session."""
        topic_stats = {}
        
        for message in self.messages:
            topic = message.topic_name
            if topic not in topic_stats:
                topic_stats[topic] = {
                    'message_type': message.message_type,
                    'count': 0,
                    'total_size': 0,
                    'first_timestamp': float('inf'),
                    'last_timestamp': 0,
                    'avg_size': 0
                }
            
            stats = topic_stats[topic]
            stats['count'] += 1
            stats['total_size'] += message.data_size
            stats['first_timestamp'] = min(stats['first_timestamp'], message.timestamp)
            stats['last_timestamp'] = max(stats['last_timestamp'], message.timestamp)
        
        # Calculate averages
        for stats in topic_stats.values():
            if stats['count'] > 0:
                stats['avg_size'] = stats['total_size'] / stats['count']
        
        return topic_stats 