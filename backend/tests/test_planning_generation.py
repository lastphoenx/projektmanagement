"""Tests für KI-Planungsgenerierung (Kontext, Voraussetzungen)."""

import pytest

from app.services.planning_constants import KI_GENERATABLE_ARTIFACTS
from app.services.planning_generation_service import (
    _build_previous_context,
    _require_prerequisite,
)
from app.services.planning_service import PlanningError


def _artifacts(*filled: str) -> list[dict]:
    slugs = [
        "zielplanung",
        "projektbeschrieb",
        "psp",
        "pflichtenheft",
        "netzplan",
        "projektplan",
    ]
    return [
        {
            "slug": slug,
            "has_content": slug in filled,
            "content": f"Inhalt {slug}" if slug in filled else "",
        }
        for slug in slugs
    ]


def test_ki_generatable_includes_steps_4_to_6():
    assert "pflichtenheft" in KI_GENERATABLE_ARTIFACTS
    assert "netzplan" in KI_GENERATABLE_ARTIFACTS
    assert "projektplan" in KI_GENERATABLE_ARTIFACTS


def test_ki_generatable_includes_steps_9_and_10():
    assert "einsatzmittelplan" in KI_GENERATABLE_ARTIFACTS
    assert "risikobetrachtung" in KI_GENERATABLE_ARTIFACTS


def test_build_previous_context_includes_all_prior_artifacts():
    ctx = _build_previous_context(_artifacts("zielplanung", "projektbeschrieb"), "psp")
    assert "Zielplanung" in ctx
    assert "Projektbeschrieb" in ctx
    assert "Inhalt zielplanung" in ctx
    assert "Inhalt projektbeschrieb" in ctx
    assert "Inhalt psp" not in ctx


def test_build_previous_context_empty_when_nothing_filled():
    assert _build_previous_context(_artifacts(), "pflichtenheft") == ""


def test_require_prerequisite_blocks_pflichtenheft_without_psp():
    with pytest.raises(PlanningError) as exc:
        _require_prerequisite(_artifacts("zielplanung", "projektbeschrieb"), "pflichtenheft")
    assert exc.value.code == "missing_prerequisite"


def test_require_prerequisite_allows_pflichtenheft_with_psp():
    _require_prerequisite(_artifacts("zielplanung", "projektbeschrieb", "psp"), "pflichtenheft")


def test_require_prerequisite_blocks_projektplan_without_netzplan():
    with pytest.raises(PlanningError) as exc:
        _require_prerequisite(
            _artifacts("zielplanung", "projektbeschrieb", "psp", "pflichtenheft"),
            "projektplan",
        )
    assert exc.value.code == "missing_prerequisite"
