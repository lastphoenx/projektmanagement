"""Tests für Portfolio-Scoring."""

from app.models import PortfolioProject
from app.services.portfolio_scoring_service import PortfolioScoringService
import uuid


def _sample(**overrides) -> PortfolioProject:
    base = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        display_number=1,
        name="Test",
        strategic_alignment_score=5,
        nonfinancial_benefit_score=5,
        customer_impact_score=4,
        feasibility_score=4,
        complexity_score=2,
        time_criticality=5,
        risk_reduction_opportunity=4,
        job_size=5,
        financial_npv=30_000,
        cost_total=40_000,
        payback_months=24,
        duration_months=2,
    )
    base.update(overrides)
    return PortfolioProject(**base)


def test_derive_roi():
    assert PortfolioScoringService.derive_roi_pct(30_000, 40_000) == 75


def test_shorter_duration_increases_wsjf():
    short = _sample(duration_months=2)
    long = _sample(duration_months=9)
    assert PortfolioScoringService.calculate_wsjf(short) > PortfolioScoringService.calculate_wsjf(long)


def test_calculate_all_scores():
    project = _sample(financial_roi_pct=0)
    PortfolioScoringService.calculate_all_scores(project)
    assert project.financial_roi_pct == 75
    assert project.tier in {"A", "B", "C"}
    assert project.wsjf is not None
