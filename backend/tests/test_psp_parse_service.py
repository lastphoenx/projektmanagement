"""Tests für PSP-Parser."""

from app.services.psp_parse_service import parse_psp_work_packages, parse_pt_effort


SAMPLE_TABLE = """
| AP-ID | Bezeichnung | Phase | Verantwortlich | Aufwand (PT) |
|-------|-------------|-------|----------------|--------------|
| AP1.1 | Analyse | Init | PM | 5 |
| AP1.2 | Konzept | Init | Dev | 10 |
"""


def test_parse_table_work_packages():
    packages = parse_psp_work_packages(SAMPLE_TABLE)
    assert len(packages) == 2
    assert packages[0].ap_id == "AP1.1"
    assert packages[0].title == "Analyse"
    assert packages[0].effort_pt == "5"
    assert packages[1].responsible == "Dev"


def test_parse_pt_effort():
    assert parse_pt_effort("10 PT") == 10
    assert parse_pt_effort("") == 0
    assert parse_pt_effort("ca. 3") == 3
