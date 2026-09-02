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
    ("PortfolioProject", "name_encrypted"): FieldClassification(
        "PortfolioProject", "name_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PortfolioProject", "sponsor_encrypted"): FieldClassification(
        "PortfolioProject", "sponsor_encrypted", DataClassification.CONFIDENTIAL, gdpr_personal=True
    ),
    ("PortfolioProject", "objective_1_encrypted"): FieldClassification(
        "PortfolioProject", "objective_1_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PortfolioProject", "objective_2_encrypted"): FieldClassification(
        "PortfolioProject", "objective_2_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PortfolioProject", "objective_3_encrypted"): FieldClassification(
        "PortfolioProject", "objective_3_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("PortfolioProject", "financial_encrypted"): FieldClassification(
        "PortfolioProject", "financial_encrypted", DataClassification.CONFIDENTIAL
    ),
    ("User", "encrypted_profile"): FieldClassification(
        "User", "encrypted_profile", DataClassification.SECRET, gdpr_personal=True
    ),
    ("User", "email_hash"): FieldClassification(
        "User", "email_hash", DataClassification.SECRET, gdpr_personal=True
    ),
    ("User", "password_hash"): FieldClassification(
        "User", "password_hash", DataClassification.SECRET, gdpr_personal=True
    ),
    ("User", "encryption_salt"): FieldClassification(
        "User", "encryption_salt", DataClassification.SECRET, gdpr_personal=True
    ),
    ("User", "totp_secret_encrypted"): FieldClassification(
        "User", "totp_secret_encrypted", DataClassification.SECRET, gdpr_personal=True
    ),
    ("UserSession", "token_hash"): FieldClassification(
        "UserSession", "token_hash", DataClassification.SECRET, gdpr_personal=True
    ),
    ("RecoveryCode", "code_hash"): FieldClassification(
        "RecoveryCode", "code_hash", DataClassification.SECRET, gdpr_personal=True
    ),
    ("LoginChallenge", "token_hash"): FieldClassification(
        "LoginChallenge", "token_hash", DataClassification.SECRET, gdpr_personal=True
    ),
    ("ProjectMember", "user_id"): FieldClassification(
        "ProjectMember", "user_id", DataClassification.INTERNAL, gdpr_personal=True
    ),
    ("AuditLog", "actor_id"): FieldClassification(
        "AuditLog", "actor_id", DataClassification.INTERNAL, gdpr_personal=True
    ),
    ("AuditLog", "detail"): FieldClassification(
        "AuditLog", "detail", DataClassification.INTERNAL, gdpr_personal=True
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
