"""CRUD operations for ROS Domain."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.ros_domain import ROSDomain
from app.schemas.ros_domain import ROSDomainCreate, ROSDomainUpdate


class CRUDROSDomain(CRUDBase[ROSDomain, ROSDomainCreate, ROSDomainUpdate]):
    """CRUD operations for ROS Domain."""

    def get_by_name(self, db: Session, *, name: str) -> Optional[ROSDomain]:
        """Get domain by name."""
        return db.query(ROSDomain).filter(ROSDomain.name == name).first()

    def get_active_domains(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ROSDomain]:
        """Get active domains."""
        return (
            db.query(ROSDomain)
            .filter(ROSDomain.agent_status == "active")
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, db: Session, *, status: str, skip: int = 0, limit: int = 100) -> List[ROSDomain]:
        """Get domains by status."""
        return (
            db.query(ROSDomain)
            .filter(ROSDomain.agent_status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(self, db: Session, *, domain_id: int, status: str) -> Optional[ROSDomain]:
        """Update domain status."""
        domain = self.get(db, id=domain_id)
        if domain:
            domain.agent_status = status
            db.add(domain)
            db.commit()
            db.refresh(domain)
        return domain


ros_domain = CRUDROSDomain(ROSDomain) 