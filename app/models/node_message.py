"""Node Message model."""

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class NodeMessage(Base):
    """Node Message model."""
    
    __tablename__ = "node_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("node_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    message_type = Column(String(100))
    payload = Column(JSON)
    timestamp = Column(DateTime, default=func.current_timestamp(), index=True)
    
    # Relationships
    connection = relationship("NodeConnection", back_populates="messages")
    
    def __repr__(self):
        return f"<NodeMessage(id={self.id}, connection_id={self.connection_id}, type='{self.message_type}')>" 