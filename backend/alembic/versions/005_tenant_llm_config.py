"""Phase 4c – Tenant LLM-Konfiguration

Revision ID: 005
Revises: 004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_llm_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="openai"),
        sa.Column("model", sa.String(length=128), nullable=False, server_default="gpt-4o-mini"),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("api_key_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("classification", sa.SmallInteger(), nullable=False, server_default=sa.text("3")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tenant_llm_configs_tenant_active",
        "tenant_llm_configs",
        ["tenant_id", "is_active"],
    )
    op.alter_column("tenant_llm_configs", "provider", server_default=None)
    op.alter_column("tenant_llm_configs", "model", server_default=None)
    op.alter_column("tenant_llm_configs", "is_active", server_default=None)
    op.alter_column("tenant_llm_configs", "classification", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_tenant_llm_configs_tenant_active", table_name="tenant_llm_configs")
    op.drop_table("tenant_llm_configs")
