"""Node Connection model."""

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class NodeConnection(Base):
    """Node Connection model."""
    
    __tablename__ = "node_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_type = Column(String(50), nullable=False)  # 'publisher', 'subscriber', 'client', 'server'
    status = Column(String(50), default="active", index=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="source_connections")
    target_node = relationship("Node", foreign_keys=[target_node_id], back_populates="target_connections")
    messages = relationship("NodeMessage", back_populates="connection", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('source_node_id', 'target_node_id', 'connection_type', name='uq_connection'),
    )
    
    def __repr__(self):
        return f"<NodeConnection(id={self.id}, source={self.source_node_id}, target={self.target_node_id}, type='{self.connection_type}')>" 