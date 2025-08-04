"""CRUD operations for Node."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate


class CRUDNode(CRUDBase[Node, NodeCreate, NodeUpdate]):
    """CRUD operations for Node."""

    def get_by_domain(self, db: Session, *, domain_id: int, skip: int = 0, limit: int = 100) -> List[Node]:
        """Get nodes by domain ID."""
        return (
            db.query(Node)
            .filter(Node.domain_id == domain_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(self, db: Session, *, node_type: str, skip: int = 0, limit: int = 100) -> List[Node]:
        """Get nodes by type."""
        return (
            db.query(Node)
            .filter(Node.node_type == node_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, db: Session, *, status: str, skip: int = 0, limit: int = 100) -> List[Node]:
        """Get nodes by status."""
        return (
            db.query(Node)
            .filter(Node.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_domain_and_type(
        self, db: Session, *, domain_id: int, node_type: str, skip: int = 0, limit: int = 100
    ) -> List[Node]:
        """Get nodes by domain ID and type."""
        return (
            db.query(Node)
            .filter(Node.domain_id == domain_id, Node.node_type == node_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name_and_domain(self, db: Session, *, name: str, domain_id: int) -> Optional[Node]:
        """Get node by name and domain ID."""
        return (
            db.query(Node)
            .filter(Node.name == name, Node.domain_id == domain_id)
            .first()
        )

    def update_status(self, db: Session, *, node_id: int, status: str) -> Optional[Node]:
        """Update node status."""
        node = self.get(db, id=node_id)
        if node:
            node.status = status
            db.add(node)
            db.commit()
            db.refresh(node)
        return node


node = CRUDNode(Node) 