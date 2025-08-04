"""CRUD operations for Node Message."""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.node_message import NodeMessage
from app.schemas.node_message import NodeMessageCreate, NodeMessageUpdate


class CRUDNodeMessage(CRUDBase[NodeMessage, NodeMessageCreate, NodeMessageUpdate]):
    """CRUD operations for Node Message."""

    def get_by_connection(self, db: Session, *, connection_id: int, skip: int = 0, limit: int = 100) -> List[NodeMessage]:
        """Get messages by connection ID."""
        return (
            db.query(NodeMessage)
            .filter(NodeMessage.connection_id == connection_id)
            .order_by(NodeMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_message_type(self, db: Session, *, message_type: str, skip: int = 0, limit: int = 100) -> List[NodeMessage]:
        """Get messages by type."""
        return (
            db.query(NodeMessage)
            .filter(NodeMessage.message_type == message_type)
            .order_by(NodeMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_messages(self, db: Session, *, hours: int = 1, skip: int = 0, limit: int = 100) -> List[NodeMessage]:
        """Get recent messages within specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(NodeMessage)
            .filter(NodeMessage.timestamp >= cutoff_time)
            .order_by(NodeMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_timerange(
        self, db: Session, *, start_time: datetime, end_time: datetime, skip: int = 0, limit: int = 100
    ) -> List[NodeMessage]:
        """Get messages within a time range."""
        return (
            db.query(NodeMessage)
            .filter(NodeMessage.timestamp >= start_time, NodeMessage.timestamp <= end_time)
            .order_by(NodeMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest_message(self, db: Session, *, connection_id: int) -> Optional[NodeMessage]:
        """Get the latest message for a connection."""
        return (
            db.query(NodeMessage)
            .filter(NodeMessage.connection_id == connection_id)
            .order_by(NodeMessage.timestamp.desc())
            .first()
        )


node_message = CRUDNodeMessage(NodeMessage) 