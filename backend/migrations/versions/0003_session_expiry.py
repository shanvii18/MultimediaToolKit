"""Add access_keys.expires_at (sign-in session tokens expire; legacy keys stay valid).

Revision ID: 0003_session_expiry
Revises: 0002_job_progress_message
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_session_expiry"
down_revision = "0002_job_progress_message"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Very old (pre-Alembic) databases get access_keys created from the current model while being
    # brought to the baseline, so the column may already exist.
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("access_keys")}
    if "expires_at" in existing:
        return
    with op.batch_alter_table("access_keys") as batch:
        batch.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("access_keys") as batch:
        batch.drop_column("expires_at")
