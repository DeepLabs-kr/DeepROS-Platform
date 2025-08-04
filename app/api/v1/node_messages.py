"""Node Message API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.node_message import node_message
from app.crud.node_connection import node_connection
from app.schemas.node_message import (
    NodeMessageCreate,
    NodeMessageResponse,
    NodeMessageWithConnection
)

router = APIRouter()


@router.post("/", response_model=NodeMessageResponse, status_code=201)
def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: NodeMessageCreate
):
    """Create a new node message."""
    # Check if connection exists
    connection = node_connection.get(db, id=message_in.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    message = node_message.create(db, obj_in=message_in)
    return message


@router.get("/", response_model=List[NodeMessageResponse])
def read_messages(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    connection_id: Optional[int] = Query(None, description="Filter by connection ID"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    hours: Optional[int] = Query(None, ge=1, le=168, description="Get messages from last N hours")
):
    """Retrieve messages with optional filtering."""
    if connection_id:
        messages = node_message.get_by_connection(
            db, connection_id=connection_id, skip=skip, limit=limit
        )
    elif message_type:
        messages = node_message.get_by_message_type(
            db, message_type=message_type, skip=skip, limit=limit
        )
    elif hours:
        messages = node_message.get_recent_messages(
            db, hours=hours, skip=skip, limit=limit
        )
    else:
        messages = node_message.get_multi(db, skip=skip, limit=limit)
    return messages


@router.get("/by-connection/{connection_id}", response_model=List[NodeMessageResponse])
def read_messages_by_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve messages by connection ID."""
    # Check if connection exists
    connection = node_connection.get(db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    messages = node_message.get_by_connection(
        db, connection_id=connection_id, skip=skip, limit=limit
    )
    return messages


@router.get("/by-type/{message_type}", response_model=List[NodeMessageResponse])
def read_messages_by_type(
    *,
    db: Session = Depends(get_db),
    message_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve messages by type."""
    messages = node_message.get_by_message_type(
        db, message_type=message_type, skip=skip, limit=limit
    )
    return messages


@router.get("/recent", response_model=List[NodeMessageResponse])
def read_recent_messages(
    db: Session = Depends(get_db),
    hours: int = Query(1, ge=1, le=168, description="Hours to look back"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve recent messages."""
    messages = node_message.get_recent_messages(
        db, hours=hours, skip=skip, limit=limit
    )
    return messages


@router.get("/{message_id}", response_model=NodeMessageResponse)
def read_message(
    *,
    db: Session = Depends(get_db),
    message_id: int
):
    """Get a specific message by ID."""
    message = node_message.get(db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("/{message_id}/with-connection", response_model=NodeMessageWithConnection)
def read_message_with_connection(
    *,
    db: Session = Depends(get_db),
    message_id: int
):
    """Get a message with connection information."""
    message = node_message.get(db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/{message_id}", response_model=NodeMessageResponse)
def delete_message(
    *,
    db: Session = Depends(get_db),
    message_id: int
):
    """Delete a message."""
    message = node_message.get(db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message = node_message.remove(db, id=message_id)
    return message 