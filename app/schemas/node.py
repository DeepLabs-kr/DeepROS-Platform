"""Node schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NodeBase(BaseModel):
    """Base Node schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Node name")
    domain_id: int = Field(..., gt=0, description="Domain ID")
    node_type: str = Field(..., description="Node type: topic, service, or action")
    status: str = Field("inactive", description="Node status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Node metadata")


class NodeCreate(NodeBase):
    """Schema for creating a node."""
    pass


class NodeUpdate(BaseModel):
    """Schema for updating a node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    node_type: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NodeResponse(NodeBase):
    """Schema for node response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NodeWithDomain(NodeResponse):
    """Schema for node with domain information."""
    domain_name: Optional[str] = None
    domain_status: Optional[str] = None
    
    class Config:
        from_attributes = True 