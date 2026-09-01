"""Tests für PSP → Jira CSV (Phase 5.1)."""

import pytest

from app.services.jira_csv_service import (
    build_jira_csv_from_psp,
    group_by_phase,
    jira_csv_export_filename,
)
from app.services.psp_parse_service import parse_psp_work_packages

SAMPLE_PSP = """
| AP-ID | Bezeichnung | Phase | Verantwortlich | Aufwand (PT) |
|-------|-------------|-------|----------------|--------------|
| AP1.1 | Projektdefinition | Initiierung | PM | 5 |
| AP1.2 | Stakeholder-Analyse | Initiierung | PM | 3 |
| AP2.1 | Umsetzung Kern | Umsetzung | Dev | 10 |
"""


def test_parse_and_group():
    wps = parse_psp_work_packages(SAMPLE_PSP)
    assert len(wps) == 3
    phases = group_by_phase(wps)
    assert len(phases) == 2
    assert phases[0].name == "Initiierung"
    assert len(phases[0].work_packages) == 2


def test_build_csv_hierarchy():
    csv_text = build_jira_csv_from_psp("DEMO", SAMPLE_PSP, project_title="Demo Projekt")
    lines = [ln for ln in csv_text.strip().splitlines() if ln.strip()]
    assert lines[0].startswith("Work type;Summary;Work item ID")
    assert len(lines) == 6  # header + 2 epics + 3 tasks
    assert lines[1].startswith("Epic;")
    assert ";DEMO-1;" in lines[1]
    assert lines[2].startswith("Task;")
    assert "AP1.1" in lines[2]
    assert ";DEMO-2;DEMO-1;" in lines[2]


def test_empty_psp_raises():
    with pytest.raises(ValueError, match="keine Arbeitspakete"):
        build_jira_csv_from_psp("DEMO", "## Leer")


def test_export_filename():
    assert jira_csv_export_filename("OTR") == "OTR_jira_csv.csv"
