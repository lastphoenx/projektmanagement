"""Tests für Budgetplan aus PSP (Phase 5.2)."""

import pytest

from app.services.budget_plan_service import build_budgetplan_from_psp

SAMPLE_PSP = """
| AP-ID | Bezeichnung | Phase | Verantwortlich | Aufwand (PT) |
|-------|-------------|-------|----------------|--------------|
| AP1.1 | Analyse | Init | PM | 5 |
| AP1.2 | Umsetzung | Build | Dev | 20 |
"""


def test_build_budgetplan_markdown():
    md = build_budgetplan_from_psp(
        SAMPLE_PSP,
        project_title="Demo",
        project_type="new_product",
        budget_ceiling_chf=100_000,
    )
    assert "## Budgetplan" in md
    assert "Gesamtbudget" in md
    assert "100'000" in md
    assert "S-Kurve" in md
    assert "PM" in md


def test_missing_pt_raises():
    with pytest.raises(ValueError, match="keine Arbeitspakete|PT-Angaben"):
        build_budgetplan_from_psp("| AP | Titel |\n|---|---|\n| x | y |")
