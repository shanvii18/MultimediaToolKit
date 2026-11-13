"""Add jobs.idempotency_key so clients can safely retry job submission.

Revision ID: 0004_job_idempotency_key
Revises: 0003_session_expiry
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_job_idempotency_key"
down_revision = "0003_session_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("jobs")}
    if "idempotency_key" not in existing:
        with op.batch_alter_table("jobs") as batch:
            batch.add_column(sa.Column("idempotency_key", sa.String(64), nullable=True))
    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("jobs")}
    if "uq_jobs_user_idempotency" not in indexes:
        op.create_index("uq_jobs_user_idempotency", "jobs", ["user_id", "idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_jobs_user_idempotency", table_name="jobs")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("idempotency_key")
