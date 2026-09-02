"""Tests für Planungs-Vollständigkeit."""

from app.services.planning_completion_service import assess_planning_completion
from app.services.planning_constants import ARTIFACT_ORDER


def _empty_artifacts() -> list[dict]:
    return [{"slug": slug, "has_content": False, "status": "pending"} for slug in ARTIFACT_ORDER]


def test_empty_planning_is_incomplete():
    result = assess_planning_completion("", _empty_artifacts())
    assert result["is_complete"] is False
    assert result["filled_count"] == 0
    assert result["total_count"] == 1 + len(ARTIFACT_ORDER)
    assert "Projektidee" in result["missing_labels"]
    assert len(result["missing_labels"]) == result["total_count"]


def test_full_planning_is_complete():
    artifacts = [
        {"slug": slug, "has_content": True, "status": "draft"} for slug in ARTIFACT_ORDER
    ]
    result = assess_planning_completion("Unsere Projektidee.", artifacts)
    assert result["is_complete"] is True
    assert result["filled_count"] == result["total_count"]
    assert result["missing_labels"] == []


def test_approved_count_requires_artifact_approval():
    artifacts = [
        {"slug": slug, "has_content": True, "status": "approved"} for slug in ARTIFACT_ORDER
    ]
    result = assess_planning_completion("Idee", artifacts)
    assert result["is_fully_approved"] is True
    assert result["approved_count"] == result["total_count"]


def test_partial_fill_lists_missing_labels():
    artifacts = _empty_artifacts()
    artifacts[0] = {"slug": "zielplanung", "has_content": True, "status": "draft"}
    result = assess_planning_completion("Idee", artifacts)
    assert result["filled_count"] == 2
    assert "2. Projektbeschrieb" in result["missing_labels"]
