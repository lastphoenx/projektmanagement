"""Tests für Planungskonstanten und Key-Validierung."""

import pytest

from app.services.planning_constants import ARTIFACT_ORDER, PROJECT_TYPE_LABELS
from app.services.planning_service import PlanningError, normalize_project_key, validate_project_key, validate_project_type


def test_artifact_order_has_ten_steps():
    assert len(ARTIFACT_ORDER) == 10
    assert ARTIFACT_ORDER[0] == "zielplanung"
    assert ARTIFACT_ORDER[-1] == "risikobetrachtung"


def test_project_types_defined():
    assert "new_product" in PROJECT_TYPE_LABELS
    assert "other" in PROJECT_TYPE_LABELS


def test_normalize_project_key():
    assert normalize_project_key(" otr ") == "OTR"


def test_validate_project_key_ok():
    validate_project_key("OTR")
    validate_project_key("A1")


@pytest.mark.parametrize("bad_key", ["", "1ABC", "A", "abcdefghi"])
def test_validate_project_key_rejects(bad_key):
    with pytest.raises(PlanningError) as exc:
        validate_project_key(bad_key)
    assert exc.value.code == "invalid_key"


def test_validate_project_type_rejects_unknown():
    with pytest.raises(PlanningError) as exc:
        validate_project_type("unknown_type")
    assert exc.value.code == "invalid_type"
