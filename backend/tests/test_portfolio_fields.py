"""Tests für verschlüsselte Portfolio-Felder."""

import uuid

from app.core.crypto import encrypt_text_master
from app.core.crypto.portfolio_fields import (
    apply_sensitive_fields,
    read_financial,
    sensitive_fields_to_dict,
)
from app.models import PortfolioProject


def test_portfolio_sensitive_roundtrip():
    entry = PortfolioProject(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        display_number=1,
        name_encrypted=encrypt_text_master("Alpha"),
    )
    apply_sensitive_fields(
        entry,
        {
            "sponsor": "M. Müller",
            "objective_1": "Ziel A",
            "financial_npv": 100_000,
            "payback_months": 12,
            "cost_total": 200_000,
        },
    )

    data = sensitive_fields_to_dict(entry)
    assert data["name"] == "Alpha"
    assert data["sponsor"] == "M. Müller"
    assert data["objective_1"] == "Ziel A"
    assert data["financial_npv"] == 100_000
    assert data["cost_total"] == 200_000

    fin = read_financial(entry)
    assert fin["payback_months"] == 12
