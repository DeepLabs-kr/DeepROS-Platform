"""Node Message schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NodeMessageBase(BaseModel):
    """Base Node Message schema."""
    connection_id: int = Field(..., gt=0, description="Connection ID")
    message_type: Optional[str] = Field(None, max_length=100, description="Message type")
    payload: Optional[Dict[str, Any]] = Field(None, description="Message payload")


class NodeMessageCreate(NodeMessageBase):
    """Schema for creating a node message."""
    pass


class NodeMessageUpdate(BaseModel):
    """Schema for updating a node message."""
    message_type: Optional[str] = Field(None, max_length=100)
    payload: Optional[Dict[str, Any]] = None


class NodeMessageResponse(NodeMessageBase):
    """Schema for node message response."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class NodeMessageWithConnection(NodeMessageResponse):
    """Schema for node message with connection information."""
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    connection_type: Optional[str] = None
    
    class Config:
        from_attributes = True 