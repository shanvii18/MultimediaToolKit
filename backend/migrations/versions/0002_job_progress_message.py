"""Add jobs.progress_message (human-readable current processing step).

Revision ID: 0002_job_progress_message
Revises: 0001_baseline
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_job_progress_message"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch:
        batch.add_column(sa.Column("progress_message", sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("progress_message")
