"""Normalisierter Klassifizierungs-Katalog — eine Quelle der Wahrheit pro Schutzklasse."""

from dataclasses import dataclass

from app.core.crypto.classification import DataClassification


@dataclass(frozen=True, slots=True)
class ClassificationPolicy:
    """Regeln pro Schutzklasse (nicht pro Feld duplizieren)."""

    level: DataClassification
    label: str
    retention_days: int | None
    gdpr_relevant: bool
    exportable: bool
    erasure_strategy: str  # "delete" | "pseudonymize" | "retain"


CLASSIFICATION_CATALOG: dict[DataClassification, ClassificationPolicy] = {
    DataClassification.PUBLIC: ClassificationPolicy(
        level=DataClassification.PUBLIC,
        label="PUBLIC",
        retention_days=None,
        gdpr_relevant=False,
        exportable=True,
        erasure_strategy="delete",
    ),
    DataClassification.INTERNAL: ClassificationPolicy(
        level=DataClassification.INTERNAL,
        label="INTERNAL",
        retention_days=365 * 3,
        gdpr_relevant=False,
        exportable=True,
        erasure_strategy="delete",
    ),
    DataClassification.CONFIDENTIAL: ClassificationPolicy(
        level=DataClassification.CONFIDENTIAL,
        label="CONFIDENTIAL",
        retention_days=365 * 7,
        gdpr_relevant=True,
        exportable=True,
        erasure_strategy="pseudonymize",
    ),
    DataClassification.SECRET: ClassificationPolicy(
        level=DataClassification.SECRET,
        label="SECRET",
        retention_days=365 * 10,
        gdpr_relevant=True,
        exportable=False,
        erasure_strategy="pseudonymize",
    ),
}


def get_policy(level: DataClassification | int) -> ClassificationPolicy:
    if isinstance(level, int):
        level = DataClassification(level)
    return CLASSIFICATION_CATALOG[level]
