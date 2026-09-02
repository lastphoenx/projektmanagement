"""Portfolio sensitive fields — encrypt name, sponsor, objectives, financials

Revision ID: 008
Revises: 007
"""

from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.crypto import encrypt_text_master

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _encrypt_financial(npv: int, roi_pct: int, payback: int, cost_total: int) -> bytes:
    return encrypt_text_master(
        json.dumps(
            {
                "financial_npv": int(npv or 0),
                "financial_roi_pct": int(roi_pct or 0),
                "payback_months": int(payback or 0),
                "cost_total": int(cost_total or 0),
            },
            separators=(",", ":"),
        )
    )


def upgrade() -> None:
    op.add_column("portfolio_projects", sa.Column("name_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("sponsor_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_1_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_2_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_3_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("financial_encrypted", sa.LargeBinary(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, name, sponsor, objective_1, objective_2, objective_3,
                   financial_npv, financial_roi_pct, payback_months, cost_total
            FROM portfolio_projects
            """
        )
    ).fetchall()

    for row in rows:
        conn.execute(
            sa.text(
                """
                UPDATE portfolio_projects
                SET name_encrypted = :name_enc,
                    sponsor_encrypted = :sponsor_enc,
                    objective_1_encrypted = :obj1_enc,
                    objective_2_encrypted = :obj2_enc,
                    objective_3_encrypted = :obj3_enc,
                    financial_encrypted = :fin_enc
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "name_enc": encrypt_text_master(row.name or ""),
                "sponsor_enc": encrypt_text_master(row.sponsor) if row.sponsor else None,
                "obj1_enc": encrypt_text_master(row.objective_1) if row.objective_1 else None,
                "obj2_enc": encrypt_text_master(row.objective_2) if row.objective_2 else None,
                "obj3_enc": encrypt_text_master(row.objective_3) if row.objective_3 else None,
                "fin_enc": _encrypt_financial(
                    row.financial_npv,
                    row.financial_roi_pct,
                    row.payback_months,
                    row.cost_total,
                ),
            },
        )

    op.drop_column("portfolio_projects", "name")
    op.drop_column("portfolio_projects", "sponsor")
    op.drop_column("portfolio_projects", "objective_1")
    op.drop_column("portfolio_projects", "objective_2")
    op.drop_column("portfolio_projects", "objective_3")
    op.drop_column("portfolio_projects", "financial_npv")
    op.drop_column("portfolio_projects", "financial_roi_pct")
    op.drop_column("portfolio_projects", "payback_months")
    op.drop_column("portfolio_projects", "cost_total")

    op.alter_column("portfolio_projects", "name_encrypted", nullable=False)


def downgrade() -> None:
    from app.core.crypto import decrypt_text_master

    op.add_column("portfolio_projects", sa.Column("name", sa.String(length=200), nullable=True))
    op.add_column("portfolio_projects", sa.Column("sponsor", sa.String(length=100), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_1", sa.String(length=200), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_2", sa.String(length=200), nullable=True))
    op.add_column("portfolio_projects", sa.Column("objective_3", sa.String(length=200), nullable=True))
    op.add_column("portfolio_projects", sa.Column("financial_npv", sa.Integer(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("financial_roi_pct", sa.Integer(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("payback_months", sa.Integer(), nullable=True))
    op.add_column("portfolio_projects", sa.Column("cost_total", sa.Integer(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, name_encrypted, sponsor_encrypted, objective_1_encrypted,
                   objective_2_encrypted, objective_3_encrypted, financial_encrypted
            FROM portfolio_projects
            """
        )
    ).fetchall()

    for row in rows:
        fin = json.loads(decrypt_text_master(row.financial_encrypted)) if row.financial_encrypted else {}
        conn.execute(
            sa.text(
                """
                UPDATE portfolio_projects
                SET name = :name,
                    sponsor = :sponsor,
                    objective_1 = :obj1,
                    objective_2 = :obj2,
                    objective_3 = :obj3,
                    financial_npv = :npv,
                    financial_roi_pct = :roi,
                    payback_months = :payback,
                    cost_total = :cost
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "name": decrypt_text_master(row.name_encrypted) if row.name_encrypted else "",
                "sponsor": decrypt_text_master(row.sponsor_encrypted) if row.sponsor_encrypted else None,
                "obj1": decrypt_text_master(row.objective_1_encrypted) if row.objective_1_encrypted else None,
                "obj2": decrypt_text_master(row.objective_2_encrypted) if row.objective_2_encrypted else None,
                "obj3": decrypt_text_master(row.objective_3_encrypted) if row.objective_3_encrypted else None,
                "npv": int(fin.get("financial_npv", 0)),
                "roi": int(fin.get("financial_roi_pct", 0)),
                "payback": int(fin.get("payback_months", 0)),
                "cost": int(fin.get("cost_total", 0)),
            },
        )

    op.alter_column("portfolio_projects", "name", nullable=False)
    for col in ("financial_npv", "financial_roi_pct", "payback_months", "cost_total"):
        op.alter_column("portfolio_projects", col, nullable=False, server_default="0")
        op.alter_column("portfolio_projects", col, server_default=None)

    op.drop_column("portfolio_projects", "name_encrypted")
    op.drop_column("portfolio_projects", "sponsor_encrypted")
    op.drop_column("portfolio_projects", "objective_1_encrypted")
    op.drop_column("portfolio_projects", "objective_2_encrypted")
    op.drop_column("portfolio_projects", "objective_3_encrypted")
    op.drop_column("portfolio_projects", "financial_encrypted")
