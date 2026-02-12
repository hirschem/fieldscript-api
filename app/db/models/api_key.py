import uuid
from sqlalchemy import Column, String, DateTime, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR
from app.db.base import Base

class ProjectApiKeyDB(Base):
    __tablename__ = "project_api_keys"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), index=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_fingerprint = Column(String(8), nullable=False)
    name = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_project_api_keys_key_hash"),
        Index("ix_project_api_keys_project_id_revoked_at", "project_id", "revoked_at"),
    )
