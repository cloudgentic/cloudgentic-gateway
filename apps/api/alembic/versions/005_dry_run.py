"""Dry-run mode: add is_dry_run to audit_logs

Revision ID: 005
Revises: 004
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("is_dry_run", sa.Boolean, nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("audit_logs", "is_dry_run")
