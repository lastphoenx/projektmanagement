"""Tests für deterministische Ressourcenauslastung aus PSP."""

import pytest

from app.services.resource_utilization_service import build_resource_utilization_table

PSP_SAMPLE = """
| AP-ID | Arbeitspaket | Phase | Verantwortlich | PT |
|-------|--------------|-------|----------------|----|
| AP1.1 | Kickoff | Phase 1 | PM | 5 |
| AP1.2 | Analyse | Phase 1 | Analyst | 10 |
| AP2.1 | Umsetzung | Phase 2 | Dev | 20 |
"""


def test_build_resource_utilization_from_psp():
    table = build_resource_utilization_table(PSP_SAMPLE, title="OTR")
    assert "Ressourcenauslastungsplan" in table
    assert "PM" in table
    assert "Analyst" in table
    assert "Dev" in table
    assert "35" in table or "35.0" in table


def test_build_resource_utilization_rejects_empty_psp():
    with pytest.raises(ValueError, match="keine Arbeitspakete"):
        build_resource_utilization_table("")
