"""classification column on auth/RBAC tables + GDPR erasure coverage

Revision ID: 009
Revises: 008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES_INTERNAL = (
    "sessions",
    "recovery_codes",
    "login_challenges",
    "project_members",
    "user_llm_preferences",
)


def upgrade() -> None:
    for table in _TABLES_INTERNAL:
        op.add_column(
            table,
            sa.Column("classification", sa.SmallInteger(), server_default="1", nullable=False),
        )
        op.alter_column(table, "classification", server_default=None)


def downgrade() -> None:
    for table in _TABLES_INTERNAL:
        op.drop_column(table, "classification")
