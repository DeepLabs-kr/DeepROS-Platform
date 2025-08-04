from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import json
from typing import Optional, Dict, Any


class ROSMessage(Base):
    """Model for storing ROS messages."""
    
    __tablename__ = "ros_messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Message metadata
    topic_name = Column(String(255), nullable=False, index=True)
    message_type = Column(String(255), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)  # ROS time as float
    sequence_number = Column(Integer, nullable=False, default=0)
    
    # Message data
    data = Column(LargeBinary, nullable=False)  # Serialized message data
    data_size = Column(Integer, nullable=False)  # Size of data in bytes
    
    # Recording session reference
    recording_session_id = Column(Integer, ForeignKey("recording_sessions.id"), nullable=False)
    recording_session = relationship("RecordingSession", back_populates="messages")
    
    # Additional metadata
    source_node = Column(String(255), nullable=True, index=True)
    destination_node = Column(String(255), nullable=True, index=True)
    qos_profile = Column(Text, nullable=True)  # JSON string of QoS settings
    header_info = Column(Text, nullable=True)  # JSON string of header information
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_topic_timestamp', 'topic_name', 'timestamp'),
        Index('idx_session_timestamp', 'recording_session_id', 'timestamp'),
        Index('idx_message_type', 'message_type'),
        Index('idx_source_node', 'source_node'),
    )
    
    def __repr__(self):
        return f"<ROSMessage(id={self.id}, topic='{self.topic_name}', type='{self.message_type}', timestamp={self.timestamp})>"
    
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
    def header_dict(self) -> Optional[Dict[str, Any]]:
        """Get header information as dictionary."""
        if self.header_info:
            try:
                return json.loads(self.header_info)
            except json.JSONDecodeError:
                return None
        return None
    
    @header_dict.setter
    def header_dict(self, value: Optional[Dict[str, Any]]):
        """Set header information from dictionary."""
        if value is not None:
            self.header_info = json.dumps(value)
        else:
            self.header_info = None 