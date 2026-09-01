"""Admin: Sicherheits-Katalog (B.1) — nur Lesen."""

from app.core.crypto.classification import DataClassification
from app.core.crypto.classification_catalog import get_policy
from app.core.crypto.field_registry import FIELD_REGISTRY
from app.services.planning_constants import ARTIFACT_LABELS, ARTIFACT_ORDER

# Tabellen-Defaults aus SQLAlchemy-Modellen (Ebene 1)
TABLE_DEFAULTS: list[dict] = [
    {
        "model": "Project",
        "table": "projects",
        "default_classification": DataClassification.INTERNAL.name,
        "description": "Projekt-Stammdaten (Key, Typ, Metadaten)",
    },
    {
        "model": "PlanningFramework",
        "table": "planning_frameworks",
        "default_classification": DataClassification.CONFIDENTIAL.name,
        "description": "Planungskern: Idee + Budgetbasis",
    },
    {
        "model": "PlanningArtifact",
        "table": "planning_artifacts",
        "default_classification": DataClassification.CONFIDENTIAL.name,
        "description": "10 Planungsartefakte (Markdown je Schritt)",
    },
    {
        "model": "Task",
        "table": "tasks",
        "default_classification": DataClassification.INTERNAL.name,
        "description": "Legacy-Tasks (API, UI ausgeblendet)",
    },
    {
        "model": "User",
        "table": "users",
        "default_classification": DataClassification.SECRET.name,
        "description": "Benutzerprofil (verschlüsselt)",
    },
]

PLANNING_STEP_FIELDS: list[dict] = [
    {
        "step_number": 0,
        "label": "Projektidee",
        "slug": None,
        "model": "PlanningFramework",
        "field": "project_idea_encrypted",
        "table": "planning_frameworks",
    },
    {
        "step_number": None,
        "label": "Budgetbasis (PSP-Auswertung)",
        "slug": None,
        "model": "PlanningFramework",
        "field": "budget_basis_encrypted",
        "table": "planning_frameworks",
        "note": "Kein eigener Sidebar-Schritt — Panel nach PSP",
    },
]

for idx, slug in enumerate(ARTIFACT_ORDER, start=1):
    PLANNING_STEP_FIELDS.append(
        {
            "step_number": idx,
            "label": ARTIFACT_LABELS.get(slug, slug),
            "slug": slug,
            "model": "PlanningArtifact",
            "field": "content_encrypted",
            "table": "planning_artifacts",
        }
    )


def _effective_classification(model: str, field: str, table_default: str) -> str:
    entry = FIELD_REGISTRY.get((model, field))
    return entry.classification.name if entry else table_default


def get_security_catalog_state() -> dict:
    classes = []
    for level in DataClassification:
        policy = get_policy(level)
        classes.append(
            {
                "level": int(level),
                "name": level.name,
                "label": policy.label,
                "retention_days": policy.retention_days,
                "gdpr_relevant": policy.gdpr_relevant,
                "exportable": policy.exportable,
                "erasure_strategy": policy.erasure_strategy,
                "requires_master_key": level.requires_master_key,
                "requires_user_key": level.requires_user_key,
                "requires_anonymization_before_external_llm": level.requires_anonymization_before_external_llm,
                "never_leaves_infrastructure": level.never_leaves_infrastructure,
            }
        )

    table_defaults = []
    for row in TABLE_DEFAULTS:
        table_defaults.append(
            {
                **row,
                "policy_source": "classification_catalog",
            }
        )

    fields = []
    for f in FIELD_REGISTRY.values():
        table_row = next((t for t in TABLE_DEFAULTS if t["model"] == f.model), None)
        table_default = table_row["default_classification"] if table_row else "INTERNAL"
        fields.append(
            {
                "model": f.model,
                "field": f.field,
                "classification": f.classification.name,
                "table_default": table_default,
                "is_override": f.classification.name != table_default,
                "gdpr_personal": f.gdpr_personal,
            }
        )

    planning_steps = []
    for step in PLANNING_STEP_FIELDS:
        model = step["model"]
        field = step["field"]
        table_row = next((t for t in TABLE_DEFAULTS if t["model"] == model), None)
        table_default = table_row["default_classification"] if table_row else "INTERNAL"
        effective = _effective_classification(model, field, table_default)
        entry = FIELD_REGISTRY.get((model, field))
        planning_steps.append(
            {
                **step,
                "table_default": table_default,
                "effective_classification": effective,
                "has_field_override": entry is not None and entry.classification.name != table_default,
            }
        )

    return {
        "classification_catalog": classes,
        "table_defaults": table_defaults,
        "field_registry_overrides": fields,
        "planning_step_fields": planning_steps,
        "catalog_version": "B.1",
        "concept": {
            "level_1": "Schutzklassen-Katalog — Regeln pro Klasse (Retention, DSGVO, LLM, Löschung)",
            "level_2": "Tabellen-Default am SQLAlchemy-Modell (classification-Spalte)",
            "level_3": "Feld-Registry — Code-Override nur bei Abweichung vom Tabellen-Default",
        },
    }
