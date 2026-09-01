"""Feld-Registry — Override der Klassifizierung pro Model+Feld (Code-Mapping, MVP)."""

from dataclasses import dataclass

from app.core.crypto.classification import DataClassification


@dataclass(frozen=True, slots=True)
class FieldClassification:
    model: str
    field: str
    classification: DataClassification
    gdpr_personal: bool = False


# Tabellen-Defaults bleiben am Model; hier nur Abweichungen.
FIELD_REGISTRY: dict[tuple[str, str], FieldClassification] = {
    ("Project", "name_encrypted"): FieldClassification(
        "Project", "name_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("Project", "description_encrypted"): FieldClassification(
        "Project", "description_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PlanningFramework", "project_idea_encrypted"): FieldClassification(
        "PlanningFramework", "project_idea_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PlanningFramework", "budget_basis_encrypted"): FieldClassification(
        "PlanningFramework", "budget_basis_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PlanningArtifact", "content_encrypted"): FieldClassification(
        "PlanningArtifact", "content_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("Task", "title_encrypted"): FieldClassification(
        "Task", "title_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("Task", "body_encrypted"): FieldClassification(
        "Task", "body_encrypted", DataClassification.CONFIDENTIAL, gdpr_personal=False
    ),
    ("User", "encrypted_profile"): FieldClassification(
        "User", "encrypted_profile", DataClassification.SECRET, gdpr_personal=True
    ),
}


def field_classification(
    model: str,
    field: str,
    *,
    table_default: DataClassification,
) -> FieldClassification:
    entry = FIELD_REGISTRY.get((model, field))
    if entry:
        return entry
    return FieldClassification(model, field, table_default)


def gdpr_fields_for_model(model: str) -> list[FieldClassification]:
    return [f for f in FIELD_REGISTRY.values() if f.model == model and f.gdpr_personal]
