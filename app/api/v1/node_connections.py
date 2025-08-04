"""Node Connection API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.node_connection import node_connection
from app.crud.node import node
from app.schemas.node_connection import (
    NodeConnectionCreate,
    NodeConnectionUpdate,
    NodeConnectionResponse,
    NodeConnectionWithNodes
)

router = APIRouter()


@router.post("/", response_model=NodeConnectionResponse, status_code=201)
def create_connection(
    *,
    db: Session = Depends(get_db),
    connection_in: NodeConnectionCreate
):
    """Create a new node connection."""
    # Check if source node exists
    source_node = node.get(db, id=connection_in.source_node_id)
    if not source_node:
        raise HTTPException(status_code=404, detail="Source node not found")
    
    # Check if target node exists
    target_node = node.get(db, id=connection_in.target_node_id)
    if not target_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    # Check if connection already exists
    existing_connection = node_connection.get_by_nodes(
        db,
        source_node_id=connection_in.source_node_id,
        target_node_id=connection_in.target_node_id,
        connection_type=connection_in.connection_type
    )
    if existing_connection:
        raise HTTPException(
            status_code=400,
            detail="Connection already exists between these nodes with the same type"
        )
    
    connection = node_connection.create(db, obj_in=connection_in)
    return connection


@router.get("/", response_model=List[NodeConnectionResponse])
def read_connections(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_node_id: Optional[int] = Query(None, description="Filter by source node ID"),
    target_node_id: Optional[int] = Query(None, description="Filter by target node ID"),
    connection_type: Optional[str] = Query(None, description="Filter by connection type"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Retrieve connections with optional filtering."""
    if source_node_id:
        connections = node_connection.get_by_source_node(
            db, source_node_id=source_node_id, skip=skip, limit=limit
        )
    elif target_node_id:
        connections = node_connection.get_by_target_node(
            db, target_node_id=target_node_id, skip=skip, limit=limit
        )
    elif connection_type:
        connections = node_connection.get_by_connection_type(
            db, connection_type=connection_type, skip=skip, limit=limit
        )
    elif status:
        connections = node_connection.get_by_status(
            db, status=status, skip=skip, limit=limit
        )
    else:
        connections = node_connection.get_multi(db, skip=skip, limit=limit)
    return connections


@router.get("/by-source/{source_node_id}", response_model=List[NodeConnectionResponse])
def read_connections_by_source(
    *,
    db: Session = Depends(get_db),
    source_node_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve connections by source node ID."""
    # Check if source node exists
    source_node = node.get(db, id=source_node_id)
    if not source_node:
        raise HTTPException(status_code=404, detail="Source node not found")
    
    connections = node_connection.get_by_source_node(
        db, source_node_id=source_node_id, skip=skip, limit=limit
    )
    return connections


@router.get("/by-target/{target_node_id}", response_model=List[NodeConnectionResponse])
def read_connections_by_target(
    *,
    db: Session = Depends(get_db),
    target_node_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve connections by target node ID."""
    # Check if target node exists
    target_node = node.get(db, id=target_node_id)
    if not target_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    connections = node_connection.get_by_target_node(
        db, target_node_id=target_node_id, skip=skip, limit=limit
    )
    return connections


@router.get("/{connection_id}", response_model=NodeConnectionResponse)
def read_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int
):
    """Get a specific connection by ID."""
    connection = node_connection.get(db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.put("/{connection_id}", response_model=NodeConnectionResponse)
def update_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int,
    connection_in: NodeConnectionUpdate
):
    """Update a connection."""
    connection = node_connection.get(db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection = node_connection.update(db, db_obj=connection, obj_in=connection_in)
    return connection


@router.patch("/{connection_id}/status", response_model=NodeConnectionResponse)
def update_connection_status(
    *,
    db: Session = Depends(get_db),
    connection_id: int,
    status: str = Query(..., description="New status")
):
    """Update connection status."""
    connection = node_connection.update_status(db, connection_id=connection_id, status=status)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.delete("/{connection_id}", response_model=NodeConnectionResponse)
def delete_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int
):
    """Delete a connection."""
    connection = node_connection.get(db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection = node_connection.remove(db, id=connection_id)
    return connection 