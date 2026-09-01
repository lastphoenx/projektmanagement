"""Admin: Sicherheits-Katalog (B.1) — nur Lesen."""

from app.core.crypto.classification import DataClassification
from app.core.crypto.classification_catalog import CLASSIFICATION_CATALOG, get_policy
from app.core.crypto.field_registry import FIELD_REGISTRY


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

    fields = [
        {
            "model": f.model,
            "field": f.field,
            "classification": f.classification.name,
            "gdpr_personal": f.gdpr_personal,
        }
        for f in FIELD_REGISTRY.values()
    ]

    return {
        "classification_catalog": classes,
        "field_registry_overrides": fields,
        "catalog_version": "B.1",
    }
