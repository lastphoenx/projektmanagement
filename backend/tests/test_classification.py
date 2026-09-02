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


def test_table_defaults_from_models():
    from app.core.crypto.table_defaults import discover_table_classification_defaults
    from app.core.db.session import Base
    from app.models import (
        LoginChallenge,
        PlanningArtifact,
        PlanningFramework,
        Project,
        ProjectMember,
        RecoveryCode,
        Task,
        User,
        UserLlmPreference,
        UserSession,
    )

    by_model = {row.model: row for row in discover_table_classification_defaults(Base)}

    assert by_model["Project"].default_classification == DataClassification.INTERNAL.name
    assert by_model["Task"].default_classification == DataClassification.INTERNAL.name
    assert by_model["User"].default_classification == DataClassification.SECRET.name
    assert by_model["PlanningFramework"].default_classification == DataClassification.CONFIDENTIAL.name
    assert by_model["PlanningArtifact"].default_classification == DataClassification.CONFIDENTIAL.name
    assert by_model["UserSession"].default_classification == DataClassification.INTERNAL.name
    assert by_model["LoginChallenge"].default_classification == DataClassification.INTERNAL.name

    # Alle 14 App-Tabellen mit classification-Spalte
    assert len(by_model) == 14

    for cls in (
        Project,
        User,
        Task,
        PlanningFramework,
        PlanningArtifact,
        UserSession,
        RecoveryCode,
        LoginChallenge,
        ProjectMember,
        UserLlmPreference,
    ):
        assert cls.__name__ in by_model


def test_field_registry_secret_credentials():
    from app.core.crypto.field_registry import FIELD_REGISTRY

    assert FIELD_REGISTRY[("User", "password_hash")].classification == DataClassification.SECRET
    assert FIELD_REGISTRY[("UserSession", "token_hash")].classification == DataClassification.SECRET
    assert FIELD_REGISTRY[("LoginChallenge", "token_hash")].classification == DataClassification.SECRET

