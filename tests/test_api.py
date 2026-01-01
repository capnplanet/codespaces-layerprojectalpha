import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_query_and_replay():
    resp = client.post("/v1/query", json={"query": "Explain routing policy", "session_id": "s1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"]
    assert body["status"] == "success"
    trace_id = body["trace_id"]

    replay = client.get(f"/v1/replay/{trace_id}")
    assert replay.status_code == 200
    assert replay.json()["trace_id"] == trace_id
