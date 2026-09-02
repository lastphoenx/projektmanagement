"""Admin: Sicherheits-Katalog (B.1) — nur Lesen."""

from app.core.crypto.classification import DataClassification
from app.core.crypto.classification_catalog import get_policy
from app.core.crypto.field_registry import FIELD_REGISTRY
from app.core.crypto.table_defaults import table_default_name_for_model, table_defaults_as_dicts
from app.core.db.session import Base
from app.services.planning_constants import ARTIFACT_LABELS, ARTIFACT_ORDER

PLANNING_STEP_FIELDS: list[dict] = [
    {
        "step_number": 0,
        "label": "Projektidee",
        "slug": None,
        "model": "PlanningFramework",
        "field": "project_idea_encrypted",
    },
    {
        "step_number": None,
        "label": "Budgetbasis (PSP-Auswertung)",
        "slug": None,
        "model": "PlanningFramework",
        "field": "budget_basis_encrypted",
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
        }
    )


def _effective_classification(model: str, field: str, table_default: str) -> str:
    entry = FIELD_REGISTRY.get((model, field))
    return entry.classification.name if entry else table_default


def get_security_catalog_state() -> dict:
    table_defaults = table_defaults_as_dicts(Base)
    table_default_by_model = {row["model"]: row["default_classification"] for row in table_defaults}

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

    fields = []
    for f in FIELD_REGISTRY.values():
        table_default = table_default_by_model.get(f.model, "INTERNAL")
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
        table_default = table_default_name_for_model(Base, model) or "INTERNAL"
        effective = _effective_classification(model, field, table_default)
        entry = FIELD_REGISTRY.get((model, field))
        table_name = next((t["table"] for t in table_defaults if t["model"] == model), "")
        planning_steps.append(
            {
                **step,
                "table": table_name,
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
        "portfolio_metadata_notes": [
            {
                "field": "data_privacy_level",
                "model": "PortfolioProject",
                "purpose": "business_label",
                "note": (
                    "WSJF-Fragebogen-Label (Public/Internal/Confidential) — fachliche Einschätzung, "
                    "nicht identisch mit der technischen classification-Spalte (Smallint, Crypto/Retention/LLM)."
                ),
            },
            {
                "field": "compliance_criticality",
                "model": "PortfolioProject",
                "purpose": "business_label",
                "note": "Fachliches Compliance-Rating für Scoring — kein Ersatz für classification.",
            },
        ],
        "catalog_version": "B.2",
        "concept": {
            "level_1": "Schutzklassen-Katalog — Regeln pro Klasse (Retention, DSGVO, LLM, Löschung)",
            "level_2": "Tabellen-Default aus SQLAlchemy-Model (classification-Spalte, introspectiert)",
            "level_3": "Feld-Registry — Code-Override nur bei Abweichung vom Tabellen-Default",
        },
    }
