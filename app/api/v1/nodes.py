"""Node API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.node import node
from app.crud.ros_domain import ros_domain
from app.schemas.node import (
    NodeCreate,
    NodeUpdate,
    NodeResponse,
    NodeWithDomain
)

router = APIRouter()


@router.post("/", response_model=NodeResponse, status_code=201)
def create_node(
    *,
    db: Session = Depends(get_db),
    node_in: NodeCreate
):
    """Create a new node."""
    # Check if domain exists
    domain = ros_domain.get(db, id=node_in.domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Check if node with same name already exists in the domain
    existing_node = node.get_by_name_and_domain(
        db, name=node_in.name, domain_id=node_in.domain_id
    )
    if existing_node:
        raise HTTPException(
            status_code=400,
            detail=f"Node with name '{node_in.name}' already exists in domain {node_in.domain_id}"
        )
    
    node_obj = node.create(db, obj_in=node_in)
    return node_obj


@router.get("/", response_model=List[NodeResponse])
def read_nodes(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    domain_id: Optional[int] = Query(None, description="Filter by domain ID"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Retrieve nodes with optional filtering."""
    if domain_id and node_type:
        nodes_list = node.get_by_domain_and_type(
            db, domain_id=domain_id, node_type=node_type, skip=skip, limit=limit
        )
    elif domain_id:
        nodes_list = node.get_by_domain(db, domain_id=domain_id, skip=skip, limit=limit)
    elif node_type:
        nodes_list = node.get_by_type(db, node_type=node_type, skip=skip, limit=limit)
    elif status:
        nodes_list = node.get_by_status(db, status=status, skip=skip, limit=limit)
    else:
        nodes_list = node.get_multi(db, skip=skip, limit=limit)
    return nodes_list


@router.get("/by-domain/{domain_id}", response_model=List[NodeResponse])
def read_nodes_by_domain(
    *,
    db: Session = Depends(get_db),
    domain_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve nodes by domain ID."""
    # Check if domain exists
    domain = ros_domain.get(db, id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    nodes_list = node.get_by_domain(db, domain_id=domain_id, skip=skip, limit=limit)
    return nodes_list


@router.get("/by-type/{node_type}", response_model=List[NodeResponse])
def read_nodes_by_type(
    *,
    db: Session = Depends(get_db),
    node_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve nodes by type."""
    nodes_list = node.get_by_type(db, node_type=node_type, skip=skip, limit=limit)
    return nodes_list


@router.get("/{node_id}", response_model=NodeResponse)
def read_node(
    *,
    db: Session = Depends(get_db),
    node_id: int
):
    """Get a specific node by ID."""
    node_obj = node.get(db, id=node_id)
    if not node_obj:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_obj


@router.put("/{node_id}", response_model=NodeResponse)
def update_node(
    *,
    db: Session = Depends(get_db),
    node_id: int,
    node_in: NodeUpdate
):
    """Update a node."""
    node_obj = node.get(db, id=node_id)
    if not node_obj:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Check if name is being updated and if it conflicts
    if node_in.name and node_in.name != node_obj.name:
        existing_node = node.get_by_name_and_domain(
            db, name=node_in.name, domain_id=node_obj.domain_id
        )
        if existing_node:
            raise HTTPException(
                status_code=400,
                detail=f"Node with name '{node_in.name}' already exists in domain {node_obj.domain_id}"
            )
    
    node_obj = node.update(db, db_obj=node_obj, obj_in=node_in)
    return node_obj


@router.patch("/{node_id}/status", response_model=NodeResponse)
def update_node_status(
    *,
    db: Session = Depends(get_db),
    node_id: int,
    status: str = Query(..., description="New status")
):
    """Update node status."""
    node_obj = node.update_status(db, node_id=node_id, status=status)
    if not node_obj:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_obj


@router.delete("/{node_id}", response_model=NodeResponse)
def delete_node(
    *,
    db: Session = Depends(get_db),
    node_id: int
):
    """Delete a node."""
    node_obj = node.get(db, id=node_id)
    if not node_obj:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node_obj = node.remove(db, id=node_id)
    return node_obj 