"""ROS Domain model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class ROSDomain(Base):
    """ROS Domain model."""
    
    __tablename__ = "ros_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    agent_status = Column(String(50), default="inactive", index=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    nodes = relationship("Node", back_populates="domain", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ROSDomain(id={self.id}, name='{self.name}', status='{self.agent_status}')>" 