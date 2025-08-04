"""ROS Domain schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ROSDomainBase(BaseModel):
    """Base ROS Domain schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Domain name")
    description: Optional[str] = Field(None, description="Domain description")
    agent_status: str = Field("inactive", description="Agent status")


class ROSDomainCreate(ROSDomainBase):
    """Schema for creating a ROS domain."""
    pass


class ROSDomainUpdate(BaseModel):
    """Schema for updating a ROS domain."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_status: Optional[str] = None


class ROSDomainResponse(ROSDomainBase):
    """Schema for ROS domain response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ROSDomainWithNodes(ROSDomainResponse):
    """Schema for ROS domain with nodes."""
    nodes: List["NodeResponse"] = []
    
    class Config:
        from_attributes = True 