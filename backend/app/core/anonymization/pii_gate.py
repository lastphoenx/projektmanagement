"""PII-Gate — einziger Durchlass vor externen LLM-Providern (Adapter für swiss-pii-anonymizer folgt)."""

import logging

from app.core.crypto.classification import DataClassification

logger = logging.getLogger(__name__)


class PIIGateError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def gate_text(
    text: str,
    classification: DataClassification,
    *,
    provider_is_local: bool,
) -> str:
    """
    Regeln gemäss GLOBAL_ARCHITECTURE.md §6:
    - Lokal → unverändert
    - SECRET → blockiert
    - INTERNAL+ extern → anonymisieren (Stub: derzeit Durchlass mit Log-Hinweis)
    - PUBLIC → unverändert
    """
    if provider_is_local:
        return text

    if classification.never_leaves_infrastructure:
        raise PIIGateError(
            "Daten der Klasse SECRET dürfen nicht an externe KI-Dienste gesendet werden."
        )

    if classification.requires_anonymization_before_external_llm:
        # TODO: swiss-pii-anonymizer über gate.anonymize() — Phase 4c Stub
        logger.info(
            "pii_gate: anonymization stub active (classification=%s) — integrate swiss-pii-anonymizer",
            classification.name,
        )

    return text
