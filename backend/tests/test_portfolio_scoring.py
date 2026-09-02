"""Tests für Portfolio-Scoring."""

import uuid

from app.core.crypto import encrypt_text_master
from app.core.crypto.portfolio_fields import apply_sensitive_fields, read_financial
from app.models import PortfolioProject
from app.services.portfolio_scoring_service import PortfolioScoringService


def _sample(**overrides) -> PortfolioProject:
    financial_npv = overrides.pop("financial_npv", 30_000)
    cost_total = overrides.pop("cost_total", 40_000)
    payback_months = overrides.pop("payback_months", 24)
    name = overrides.pop("name", "Test")
    project = PortfolioProject(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        display_number=1,
        name_encrypted=encrypt_text_master(name),
        strategic_alignment_score=5,
        nonfinancial_benefit_score=5,
        customer_impact_score=4,
        feasibility_score=4,
        complexity_score=2,
        time_criticality=5,
        risk_reduction_opportunity=4,
        job_size=5,
        duration_months=overrides.pop("duration_months", 2),
        **overrides,
    )
    apply_sensitive_fields(
        project,
        {
            "financial_npv": financial_npv,
            "cost_total": cost_total,
            "payback_months": payback_months,
        },
    )
    return project


def test_derive_roi():
    assert PortfolioScoringService.derive_roi_pct(30_000, 40_000) == 75


def test_shorter_duration_increases_wsjf():
    short = _sample(duration_months=2)
    long = _sample(duration_months=9)
    assert PortfolioScoringService.calculate_wsjf(short) > PortfolioScoringService.calculate_wsjf(long)


def test_calculate_all_scores():
    project = _sample()
    PortfolioScoringService.calculate_all_scores(project)
    assert read_financial(project)["financial_roi_pct"] == 75
    assert project.tier in {"A", "B", "C"}
    assert project.wsjf is not None
