"""Zentrale Konstanten für Planungsschritte und Projekttypen (services/, fachlich)."""

from enum import StrEnum


class ProjectType(StrEnum):
    NEW_PRODUCT = "new_product"
    PROCESS_IMPROVEMENT = "process_improvement"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


PROJECT_TYPE_LABELS: dict[str, str] = {
    ProjectType.NEW_PRODUCT: "Neues Produkt / Feature",
    ProjectType.PROCESS_IMPROVEMENT: "Prozess-Verbesserung",
    ProjectType.INFRASTRUCTURE: "Infrastruktur",
    ProjectType.OTHER: "Sonstiges",
}

PROJECT_KEY_PATTERN = r"^[A-Z][A-Z0-9]{1,7}$"

ARTIFACT_ORDER: list[str] = [
    "zielplanung",
    "projektbeschrieb",
    "psp",
    "pflichtenheft",
    "netzplan",
    "projektplan",
    "jira_csv",
    "budgetplan",
    "einsatzmittelplan",
    "risikobetrachtung",
]

PLANNING_ARTIFACT_SLUGS = frozenset(ARTIFACT_ORDER)

# Phase 4c–6: KI-Generierung für Schritte 1–6, 9–10
KI_GENERATABLE_ARTIFACTS = frozenset(
    {
        "zielplanung",
        "projektbeschrieb",
        "psp",
        "pflichtenheft",
        "netzplan",
        "projektplan",
        "einsatzmittelplan",
        "risikobetrachtung",
    }
)

ARTIFACT_LABELS: dict[str, str] = {
    "zielplanung": "1. Zielplanung",
    "projektbeschrieb": "2. Projektbeschrieb",
    "psp": "3. Projektstrukturplan (PSP)",
    "pflichtenheft": "4. Pflichtenheft (kurz)",
    "netzplan": "5. Netzplan",
    "projektplan": "6. Projektplan (Gantt)",
    "jira_csv": "7. Jira CSV",
    "budgetplan": "8. Budgetplan",
    "einsatzmittelplan": "9. Einsatzmittelplan",
    "risikobetrachtung": "10. Risikobetrachtung",
}

ARTIFACT_STATUS_PENDING = 0
ARTIFACT_STATUS_DRAFT = 1
ARTIFACT_STATUS_APPROVED = 2

ARTIFACT_STATUS_LABELS: dict[int, str] = {
    ARTIFACT_STATUS_PENDING: "pending",
    ARTIFACT_STATUS_DRAFT: "draft",
    ARTIFACT_STATUS_APPROVED: "approved",
}

ARTIFACT_STATUS_FROM_LABEL: dict[str, int] = {
    v: k for k, v in ARTIFACT_STATUS_LABELS.items()
}
