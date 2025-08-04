"""Node Connection schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NodeConnectionBase(BaseModel):
    """Base Node Connection schema."""
    source_node_id: int = Field(..., gt=0, description="Source node ID")
    target_node_id: int = Field(..., gt=0, description="Target node ID")
    connection_type: str = Field(..., description="Connection type: publisher, subscriber, client, server")
    status: str = Field("active", description="Connection status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Connection metadata")


class NodeConnectionCreate(NodeConnectionBase):
    """Schema for creating a node connection."""
    pass


class NodeConnectionUpdate(BaseModel):
    """Schema for updating a node connection."""
    connection_type: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NodeConnectionResponse(NodeConnectionBase):
    """Schema for node connection response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class NodeConnectionWithNodes(NodeConnectionResponse):
    """Schema for node connection with node information."""
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    source_domain_name: Optional[str] = None
    target_domain_name: Optional[str] = None
    
    class Config:
        from_attributes = True 