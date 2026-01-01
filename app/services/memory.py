import redis  # type: ignore
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import MemoryItem

settings = get_settings()


class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        try:
            self.redis = redis.from_url(settings.redis_url)
            self.redis.ping()
        except Exception:
            self.redis = None
        self.ttl_seconds = 60 * 60 * 24  # 24h TTL by default
        self.max_items = 50

    def store(self, session_id: str, role: str, content: str) -> None:
        if not session_id:
            return
        if self.redis:
            key = f"session:{session_id}"
            self.redis.lpush(key, content)
            self.redis.ltrim(key, 0, self.max_items - 1)
            self.redis.expire(key, self.ttl_seconds)
        item = MemoryItem(session_id=session_id, role=role, content=content)
        self.db.add(item)
        self.db.commit()

    def fetch_recent(self, session_id: str, limit: int = 5) -> list[str]:
        if not session_id:
            return []
        if not self.redis:
            return []
        values = self.redis.lrange(f"session:{session_id}", 0, limit - 1)
        return [v.decode() for v in values]

    def summarize(self, session_id: str, limit: int = 5) -> str:
        recent = self.fetch_recent(session_id, limit)
        if not recent:
            return ""
        # simple heuristic summary
        joined = " \n".join(recent)
        return joined[:500]
