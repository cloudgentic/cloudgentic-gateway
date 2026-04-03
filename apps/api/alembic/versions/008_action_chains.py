"""Add triggered_by_chain_rule_id column to audit_logs for action chain tracking

Revision ID: 008
Revises: 007
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column(
            "triggered_by_chain_rule_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_audit_logs_chain_rule_id",
        "audit_logs",
        ["triggered_by_chain_rule_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_chain_rule_id", table_name="audit_logs")
    op.drop_column("audit_logs", "triggered_by_chain_rule_id")
