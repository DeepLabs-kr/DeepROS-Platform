"""ROS Domain API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.ros_domain import ros_domain
from app.schemas.ros_domain import (
    ROSDomainCreate,
    ROSDomainUpdate,
    ROSDomainResponse,
    ROSDomainWithNodes
)

router = APIRouter()


@router.post("/", response_model=ROSDomainResponse, status_code=201)
def create_domain(
    *,
    db: Session = Depends(get_db),
    domain_in: ROSDomainCreate
):
    """Create a new ROS domain."""
    # Check if domain with same name already exists
    existing_domain = ros_domain.get_by_name(db, name=domain_in.name)
    if existing_domain:
        raise HTTPException(
            status_code=400,
            detail=f"Domain with name '{domain_in.name}' already exists"
        )
    
    domain = ros_domain.create(db, obj_in=domain_in)
    return domain


@router.get("/", response_model=List[ROSDomainResponse])
def read_domains(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by agent status")
):
    """Retrieve domains with optional filtering."""
    if status:
        domains = ros_domain.get_by_status(db, status=status, skip=skip, limit=limit)
    else:
        domains = ros_domain.get_multi(db, skip=skip, limit=limit)
    return domains


@router.get("/active", response_model=List[ROSDomainResponse])
def read_active_domains(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Retrieve active domains."""
    domains = ros_domain.get_active_domains(db, skip=skip, limit=limit)
    return domains


@router.get("/{domain_id}", response_model=ROSDomainResponse)
def read_domain(
    *,
    db: Session = Depends(get_db),
    domain_id: int
):
    """Get a specific domain by ID."""
    domain = ros_domain.get(db, id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.get("/{domain_id}/with-nodes", response_model=ROSDomainWithNodes)
def read_domain_with_nodes(
    *,
    db: Session = Depends(get_db),
    domain_id: int
):
    """Get a domain with its nodes."""
    domain = ros_domain.get(db, id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.put("/{domain_id}", response_model=ROSDomainResponse)
def update_domain(
    *,
    db: Session = Depends(get_db),
    domain_id: int,
    domain_in: ROSDomainUpdate
):
    """Update a domain."""
    domain = ros_domain.get(db, id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Check if name is being updated and if it conflicts
    if domain_in.name and domain_in.name != domain.name:
        existing_domain = ros_domain.get_by_name(db, name=domain_in.name)
        if existing_domain:
            raise HTTPException(
                status_code=400,
                detail=f"Domain with name '{domain_in.name}' already exists"
            )
    
    domain = ros_domain.update(db, db_obj=domain, obj_in=domain_in)
    return domain


@router.patch("/{domain_id}/status", response_model=ROSDomainResponse)
def update_domain_status(
    *,
    db: Session = Depends(get_db),
    domain_id: int,
    status: str = Query(..., description="New status")
):
    """Update domain status."""
    domain = ros_domain.update_status(db, domain_id=domain_id, status=status)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.delete("/{domain_id}", response_model=ROSDomainResponse)
def delete_domain(
    *,
    db: Session = Depends(get_db),
    domain_id: int
):
    """Delete a domain."""
    domain = ros_domain.get(db, id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    domain = ros_domain.remove(db, id=domain_id)
    return domain 