"""Node model."""

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Node(Base):
    """Node model."""
    
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    domain_id = Column(Integer, ForeignKey("ros_domains.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)  # 'topic', 'service', 'action'
    status = Column(String(50), default="inactive", index=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    domain = relationship("ROSDomain", back_populates="nodes")
    source_connections = relationship(
        "NodeConnection", 
        foreign_keys="NodeConnection.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    target_connections = relationship(
        "NodeConnection",
        foreign_keys="NodeConnection.target_node_id", 
        back_populates="target_node",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}', type='{self.node_type}', status='{self.status}')>" 