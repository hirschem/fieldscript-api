from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime
from app.db.models.api_key import ProjectApiKeyDB
from app.schemas.api_key import ProjectApiKey
from app.security.api_keys import generate_api_key, hash_api_key, key_prefix
import hmac

class SqlApiKeyStore:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: str, name: Optional[str] = None) -> Tuple[str, ProjectApiKey]:
        raw_key = generate_api_key()
        prefix = key_prefix(raw_key)
        key_hash = hash_api_key(raw_key)
        fingerprint = key_hash[-8:]
        db_obj = ProjectApiKeyDB(
            project_id=project_id,
            key_prefix=prefix,
            key_hash=key_hash,
            key_fingerprint=fingerprint,
            name=name
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return raw_key, self._to_schema(db_obj)

    def list(self, project_id: str) -> List[ProjectApiKey]:
        q = self.db.query(ProjectApiKeyDB).filter(ProjectApiKeyDB.project_id == project_id).order_by(ProjectApiKeyDB.created_at.desc())
        return [self._to_schema(row) for row in q.all()]

    def revoke(self, project_id: str, key_id: str) -> Optional[ProjectApiKey]:
        row = self.db.query(ProjectApiKeyDB).filter(ProjectApiKeyDB.id == key_id).first()
        if not row or row.project_id != project_id:
            return None
        if row.revoked_at is None:
            row.revoked_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(row)
        return self._to_schema(row)

    def verify(self, raw_key: str) -> Optional[ProjectApiKey]:
        if not raw_key:
            return None
        candidate_hash = hash_api_key(raw_key)
        row = self.db.query(ProjectApiKeyDB).filter(
            ProjectApiKeyDB.key_hash == candidate_hash,
            ProjectApiKeyDB.revoked_at.is_(None)
        ).first()
        if not row:
            return None
        # Optional: constant-time compare
        if not hmac.compare_digest(row.key_hash, candidate_hash):
            return None
        # Best-effort update last_used_at
        try:
            row.last_used_at = datetime.utcnow()
            self.db.commit()
        except Exception:
            self.db.rollback()
        return self._to_schema(row)

    def _to_schema(self, row: ProjectApiKeyDB) -> ProjectApiKey:
        return ProjectApiKey(
            id=row.id,
            project_id=row.project_id,
            key_prefix=row.key_prefix,
            key_fingerprint=row.key_fingerprint,
            name=row.name,
            created_at=row.created_at,
            last_used_at=row.last_used_at,
            revoked_at=row.revoked_at
        )
