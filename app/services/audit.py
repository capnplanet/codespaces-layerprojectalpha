import json

from sqlalchemy.orm import Session

from app.core.security import sign_hmac
from app.models.models import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(self, trace_id: str, event: str, payload) -> None:
        serialized = json.dumps(payload, sort_keys=True)
        signature = sign_hmac(serialized)
        log = AuditLog(trace_id=trace_id, event=event, payload=payload, hmac=signature)
        self.db.add(log)
        self.db.commit()
