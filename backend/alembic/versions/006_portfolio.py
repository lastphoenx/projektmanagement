"""Portfolio projects with WSJF scoring

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sponsor", sa.String(length=100), nullable=True),
        sa.Column("business_unit", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("objective_1", sa.String(length=200), nullable=True),
        sa.Column("objective_2", sa.String(length=200), nullable=True),
        sa.Column("objective_3", sa.String(length=200), nullable=True),
        sa.Column("strategic_alignment_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("nonfinancial_benefit_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("customer_impact_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("feasibility_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("complexity_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("risk_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cybersecurity_risk_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("compliance_criticality", sa.String(length=50), nullable=True),
        sa.Column("data_privacy_level", sa.String(length=50), nullable=True),
        sa.Column("financial_npv", sa.Integer(), server_default="0", nullable=False),
        sa.Column("financial_roi_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("payback_months", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cost_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("time_criticality", sa.Integer(), server_default="0", nullable=False),
        sa.Column("risk_reduction_opportunity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("job_size", sa.Integer(), server_default="1", nullable=False),
        sa.Column("dependencies_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duration_months", sa.Integer(), server_default="0", nullable=False),
        sa.Column("resource_demand_fte", sa.Integer(), server_default="0", nullable=False),
        sa.Column("strategic_importance", sa.Float(), nullable=True),
        sa.Column("feasibility_index", sa.Float(), nullable=True),
        sa.Column("value_score", sa.Float(), nullable=True),
        sa.Column("wsjf", sa.Float(), nullable=True),
        sa.Column("composite_score", sa.Float(), nullable=True),
        sa.Column("tier", sa.String(length=1), nullable=True),
        sa.Column("matrix_quadrant", sa.String(length=32), nullable=True),
        sa.Column("classification", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(
        "ix_portfolio_projects_tenant_display",
        "portfolio_projects",
        ["tenant_id", "display_number"],
        unique=True,
    )
    for col in (
        "strategic_alignment_score",
        "nonfinancial_benefit_score",
        "customer_impact_score",
        "feasibility_score",
        "complexity_score",
        "risk_score",
        "cybersecurity_risk_score",
        "financial_npv",
        "financial_roi_pct",
        "payback_months",
        "cost_total",
        "time_criticality",
        "risk_reduction_opportunity",
        "job_size",
        "dependencies_count",
        "duration_months",
        "resource_demand_fte",
        "classification",
    ):
        op.alter_column("portfolio_projects", col, server_default=None)


def downgrade() -> None:
    op.drop_index("ix_portfolio_projects_tenant_display", table_name="portfolio_projects")
    op.drop_table("portfolio_projects")
