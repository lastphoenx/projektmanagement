"""Phase 4 – Projekt-Key, Projekttyp, Planungskern

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ARTIFACT_SLUGS = [
    "zielplanung",
    "projektbeschrieb",
    "psp",
    "pflichtenheft",
    "netzplan",
    "projektplan",
    "jira_csv",
    "budgetplan",
    "einsatzmittelplan",
    "risikobetrachtung",
]


def upgrade() -> None:
    op.add_column("projects", sa.Column("key", sa.String(length=8), nullable=True))
    op.add_column(
        "projects",
        sa.Column("project_type", sa.String(length=32), nullable=False, server_default="other"),
    )

    # Bestehende Projekte: Key aus UUID-Präfix (tenant-weit eindeutig)
    op.execute(
        sa.text(
            """
            UPDATE projects
            SET key = UPPER(SUBSTRING(REPLACE(id::text, '-', '') FROM 1 FOR 8))
            WHERE key IS NULL
            """
        )
    )

    op.alter_column("projects", "key", nullable=False)
    op.alter_column("projects", "project_type", server_default=None)
    op.create_index("ix_projects_tenant_key", "projects", ["tenant_id", "key"], unique=True)

    op.create_table(
        "planning_frameworks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_idea_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("budget_basis_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("revision", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("classification", sa.SmallInteger(), nullable=False, server_default=sa.text("2")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.alter_column("planning_frameworks", "revision", server_default=None)
    op.alter_column("planning_frameworks", "classification", server_default=None)

    op.create_table(
        "planning_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("framework_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("content_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classification", sa.SmallInteger(), nullable=False, server_default=sa.text("2")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["framework_id"], ["planning_frameworks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_planning_artifacts_framework_slug",
        "planning_artifacts",
        ["framework_id", "slug"],
        unique=True,
    )
    op.alter_column("planning_artifacts", "status", server_default=None)
    op.alter_column("planning_artifacts", "version", server_default=None)
    op.alter_column("planning_artifacts", "classification", server_default=None)

    # Framework für bestehende Projekte
    op.execute(
        sa.text(
            """
            INSERT INTO planning_frameworks (id, project_id, revision, classification, created_at, updated_at)
            SELECT gen_random_uuid(), p.id, 1, 2, now(), now()
            FROM projects p
            WHERE NOT EXISTS (
                SELECT 1 FROM planning_frameworks pf WHERE pf.project_id = p.id
            )
            """
        )
    )

    for slug in ARTIFACT_SLUGS:
        slug_literal = slug.replace("'", "''")
        op.execute(
            sa.text(
                f"""
                INSERT INTO planning_artifacts (id, framework_id, slug, status, version, classification, created_at, updated_at)
                SELECT gen_random_uuid(), pf.id, '{slug_literal}', 0, 0, 2, now(), now()
                FROM planning_frameworks pf
                WHERE NOT EXISTS (
                    SELECT 1 FROM planning_artifacts pa
                    WHERE pa.framework_id = pf.id AND pa.slug = '{slug_literal}'
                )
                """
            )
        )


def downgrade() -> None:
    op.drop_index("ix_planning_artifacts_framework_slug", table_name="planning_artifacts")
    op.drop_table("planning_artifacts")
    op.drop_table("planning_frameworks")
    op.drop_index("ix_projects_tenant_key", table_name="projects")
    op.drop_column("projects", "project_type")
    op.drop_column("projects", "key")
