from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.sql import func
from ..database import Base
from typing import Optional


class MessageIndex(Base):
    """Model for indexing messages for efficient searching and retrieval."""
    
    __tablename__ = "message_index"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Message reference
    message_id = Column(Integer, nullable=False, index=True)
    
    # Indexing fields
    topic_name = Column(String(255), nullable=False, index=True)
    message_type = Column(String(255), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)  # ROS time as float
    recording_session_id = Column(Integer, nullable=False, index=True)
    
    # Time-based indexing
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    day = Column(Integer, nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    minute = Column(Integer, nullable=False, index=True)
    second = Column(Integer, nullable=False, index=True)
    
    # Content indexing
    source_node = Column(String(255), nullable=True, index=True)
    destination_node = Column(String(255), nullable=True, index=True)
    
    # Size and metadata
    data_size = Column(Integer, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False, default=0)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_topic_time', 'topic_name', 'timestamp'),
        Index('idx_session_time', 'recording_session_id', 'timestamp'),
        Index('idx_type_time', 'message_type', 'timestamp'),
        Index('idx_date_time', 'year', 'month', 'day', 'hour', 'minute'),
        Index('idx_size_time', 'data_size', 'timestamp'),
        Index('idx_source_time', 'source_node', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MessageIndex(id={self.id}, message_id={self.message_id}, topic='{self.topic_name}', timestamp={self.timestamp})>"
    
    @classmethod
    def from_message(cls, message, recording_session_id: int):
        """Create an index entry from a ROSMessage."""
        from datetime import datetime
        
        # Convert ROS timestamp to datetime for time-based indexing
        dt = datetime.fromtimestamp(message.timestamp)
        
        return cls(
            message_id=message.id,
            topic_name=message.topic_name,
            message_type=message.message_type,
            timestamp=message.timestamp,
            recording_session_id=recording_session_id,
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            source_node=message.source_node,
            destination_node=message.destination_node,
            data_size=message.data_size,
            sequence_number=message.sequence_number
        ) 