"""Security fixes: password_changed_at, unique constraint on connected_accounts

Revision ID: 003
Revises: 002
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_changed_at for JWT revocation on password change
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))

    # Add unique constraint to prevent duplicate connected accounts
    op.create_unique_constraint(
        "uq_connected_accounts_user_provider_account",
        "connected_accounts",
        ["user_id", "provider", "provider_account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_connected_accounts_user_provider_account", "connected_accounts")
    op.drop_column("users", "password_changed_at")
