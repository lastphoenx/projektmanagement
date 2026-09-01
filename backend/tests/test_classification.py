"""Tests für Klassifizierungs-Katalog und Feld-Registry."""

from app.core.crypto.classification import DataClassification
from app.core.crypto.classification_catalog import CLASSIFICATION_CATALOG, get_policy
from app.core.crypto.field_registry import field_classification, gdpr_fields_for_model


def test_classification_catalog_covers_all_levels():
    for level in DataClassification:
        assert level in CLASSIFICATION_CATALOG
        policy = get_policy(level)
        assert policy.level == level
        assert policy.label == level.name


def test_secret_policy_requires_pseudonymize_on_erasure():
    policy = get_policy(DataClassification.SECRET)
    assert policy.gdpr_relevant is True
    assert policy.exportable is False
    assert policy.erasure_strategy == "pseudonymize"


def test_field_registry_override():
    field = field_classification(
        "PlanningArtifact",
        "content_encrypted",
        table_default=DataClassification.INTERNAL,
    )
    assert field.classification == DataClassification.CONFIDENTIAL


def test_field_registry_fallback_to_table_default():
    field = field_classification(
        "Project",
        "version",
        table_default=DataClassification.INTERNAL,
    )
    assert field.classification == DataClassification.INTERNAL


def test_gdpr_fields_for_user():
    fields = gdpr_fields_for_model("User")
    assert any(f.field == "encrypted_profile" for f in fields)
