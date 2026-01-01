import redis
from app.core.config import get_settings
from app.models.models import MemoryItem
from sqlalchemy.orm import Session

settings = get_settings()


class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        try:
            self.redis = redis.from_url(settings.redis_url)
            self.redis.ping()
        except Exception:
            self.redis = None

    def store(self, session_id: str, role: str, content: str) -> None:
        if not session_id:
            return
        if self.redis:
            self.redis.lpush(f"session:{session_id}", content)
        item = MemoryItem(session_id=session_id, role=role, content=content)
        self.db.add(item)
        self.db.commit()

    def fetch_recent(self, session_id: str, limit: int = 5):
        if not session_id:
            return []
        if not self.redis:
            return []
        values = self.redis.lrange(f"session:{session_id}", 0, limit - 1)
        return [v.decode() for v in values]
