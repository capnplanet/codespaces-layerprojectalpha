from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from app.core.database import Base


class Trace(Base):
    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True)
    input = Column(JSON, nullable=False)
    normalized_input = Column(JSON, nullable=False)
    classification = Column(JSON, nullable=False)
    routing = Column(JSON, nullable=False)
    retrieval = Column(JSON, nullable=False)
    tool_calls = Column(JSON, nullable=False)
    output = Column(JSON, nullable=False)
    output_hash = Column(String, nullable=False)
    policy = Column(JSON, nullable=False)
    cost_units = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    replayable = Column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True)
    event = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    hmac = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    rules = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset = Column(String, nullable=False)
    results = Column(JSON, nullable=False)
    report_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
