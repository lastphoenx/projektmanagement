"""Tests für PII-Gate."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.anonymization.pii_gate import PIIGateError, analyze_text, gate_text
from app.core.crypto.classification import DataClassification


def test_local_provider_skips_gate():
    assert gate_text("geheim", DataClassification.SECRET, provider_is_local=True) == "geheim"


def test_secret_blocked_external():
    with pytest.raises(PIIGateError):
        gate_text("geheim", DataClassification.SECRET, provider_is_local=False)


def test_public_passes_external():
    assert gate_text("hello", DataClassification.PUBLIC, provider_is_local=False) == "hello"


def test_confidential_anonymized_external():
    fake_result = MagicMock()
    fake_result.text = "Hallo [PERSON]"
    fake_result.findings = [MagicMock()]

    with patch("swiss_pii_anonymizer.anonymize", return_value=fake_result):
        out = gate_text(
            "Hallo Maria",
            DataClassification.CONFIDENTIAL,
            provider_is_local=False,
        )
    assert out == "Hallo [PERSON]"


def test_analyze_text_with_mock():
    finding = MagicMock()
    finding.entity_type = "PERSON"
    finding.text = "Maria"
    finding.score = 0.9

    with patch("swiss_pii_anonymizer.analyze", return_value=[finding]):
        results = analyze_text("Maria Muster")
    assert len(results) == 1
    assert results[0].entity_type == "PERSON"
