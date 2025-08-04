"""CRUD operations for Node Connection."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.node_connection import NodeConnection
from app.schemas.node_connection import NodeConnectionCreate, NodeConnectionUpdate


class CRUDNodeConnection(CRUDBase[NodeConnection, NodeConnectionCreate, NodeConnectionUpdate]):
    """CRUD operations for Node Connection."""

    def get_by_source_node(self, db: Session, *, source_node_id: int, skip: int = 0, limit: int = 100) -> List[NodeConnection]:
        """Get connections by source node ID."""
        return (
            db.query(NodeConnection)
            .filter(NodeConnection.source_node_id == source_node_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_target_node(self, db: Session, *, target_node_id: int, skip: int = 0, limit: int = 100) -> List[NodeConnection]:
        """Get connections by target node ID."""
        return (
            db.query(NodeConnection)
            .filter(NodeConnection.target_node_id == target_node_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_connection_type(self, db: Session, *, connection_type: str, skip: int = 0, limit: int = 100) -> List[NodeConnection]:
        """Get connections by type."""
        return (
            db.query(NodeConnection)
            .filter(NodeConnection.connection_type == connection_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, db: Session, *, status: str, skip: int = 0, limit: int = 100) -> List[NodeConnection]:
        """Get connections by status."""
        return (
            db.query(NodeConnection)
            .filter(NodeConnection.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_nodes(
        self, db: Session, *, source_node_id: int, target_node_id: int, connection_type: str
    ) -> Optional[NodeConnection]:
        """Get connection by source, target nodes and type."""
        return (
            db.query(NodeConnection)
            .filter(
                NodeConnection.source_node_id == source_node_id,
                NodeConnection.target_node_id == target_node_id,
                NodeConnection.connection_type == connection_type
            )
            .first()
        )

    def update_status(self, db: Session, *, connection_id: int, status: str) -> Optional[NodeConnection]:
        """Update connection status."""
        connection = self.get(db, id=connection_id)
        if connection:
            connection.status = status
            db.add(connection)
            db.commit()
            db.refresh(connection)
        return connection


node_connection = CRUDNodeConnection(NodeConnection) 