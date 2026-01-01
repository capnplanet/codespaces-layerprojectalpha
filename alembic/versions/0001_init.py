from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "traces",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trace_id", sa.String, unique=True, index=True),
        sa.Column("input", sa.JSON, nullable=False),
        sa.Column("normalized_input", sa.JSON, nullable=False),
        sa.Column("classification", sa.JSON, nullable=False),
        sa.Column("routing", sa.JSON, nullable=False),
        sa.Column("retrieval", sa.JSON, nullable=False),
        sa.Column("tool_calls", sa.JSON, nullable=False),
        sa.Column("output", sa.JSON, nullable=False),
        sa.Column("output_hash", sa.String, nullable=False),
        sa.Column("policy", sa.JSON, nullable=False),
        sa.Column("cost_units", sa.Integer, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("replayable", sa.Boolean, server_default=sa.sql.expression.true()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trace_id", sa.String, index=True),
        sa.Column("event", sa.String, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("hmac", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "policy_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("version", sa.String, nullable=False),
        sa.Column("rules", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "memory_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String, index=True),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dataset", sa.String, nullable=False),
        sa.Column("results", sa.JSON, nullable=False),
        sa.Column("report_path", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("eval_runs")
    op.drop_table("memory_items")
    op.drop_table("policy_versions")
    op.drop_table("audit_logs")
    op.drop_table("traces")
