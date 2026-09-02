"""PII-Gate — einziger Durchlass vor externen LLM-Providern (Adapter für swiss-pii-anonymizer)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from app.core.crypto.classification import DataClassification

logger = logging.getLogger(__name__)


class PIIGateError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PiiFinding:
    entity_type: str
    text: str
    score: float


def analyze_text(text: str) -> list[PiiFinding]:
    """Erkennt PII ohne Text zu verändern (UI-Vorschau vor Cloud-Versand)."""
    if not text.strip() or not settings.pii_anonymizer_enabled:
        return []
    try:
        from swiss_pii_anonymizer import analyze
    except ImportError:
        if settings.pii_anonymizer_required:
            raise PIIGateError(
                "swiss-pii-anonymizer ist nicht installiert — Cloud-Versand blockiert."
            ) from None
        return []

    try:
        return [
            PiiFinding(entity_type=f.entity_type, text=f.text, score=float(f.score))
            for f in analyze(text)
        ]
    except Exception as exc:
        logger.warning("pii_gate analyze failed: %s", exc)
        if settings.pii_anonymizer_required:
            raise PIIGateError("PII-Analyse fehlgeschlagen — Cloud-Versand blockiert.") from exc
        return []


def _anonymize_text(text: str) -> str:
    if not text.strip():
        return text
    if not settings.pii_anonymizer_enabled:
        return text

    try:
        from swiss_pii_anonymizer import anonymize
    except ImportError as exc:
        if settings.pii_anonymizer_required:
            raise PIIGateError(
                "swiss-pii-anonymizer ist nicht installiert — Anonymisierung nicht möglich."
            ) from exc
        logger.warning("pii_gate: swiss-pii-anonymizer nicht installiert — Text unverändert")
        return text

    try:
        result = anonymize(text)
        findings = len(result.findings)
        if findings:
            logger.info("pii_gate: %s Fundstelle(n) anonymisiert", findings)
        return result.text
    except Exception as exc:
        logger.warning("pii_gate anonymize failed: %s", exc)
        if settings.pii_anonymizer_required:
            raise PIIGateError("PII-Anonymisierung fehlgeschlagen.") from exc
        return text


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
    - INTERNAL+ extern → anonymisieren
    - PUBLIC → unverändert
    """
    if provider_is_local:
        return text

    if classification.never_leaves_infrastructure:
        raise PIIGateError(
            "Daten der Klasse SECRET dürfen nicht an externe KI-Dienste gesendet werden."
        )

    if classification.requires_anonymization_before_external_llm:
        return _anonymize_text(text)

    return text
