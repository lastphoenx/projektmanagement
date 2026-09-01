"""Tests für PII-Gate."""

import pytest

from app.core.anonymization.pii_gate import PIIGateError, gate_text
from app.core.crypto.classification import DataClassification


def test_local_provider_skips_gate():
    assert gate_text("geheim", DataClassification.SECRET, provider_is_local=True) == "geheim"


def test_secret_blocked_external():
    with pytest.raises(PIIGateError):
        gate_text("geheim", DataClassification.SECRET, provider_is_local=False)


def test_public_passes_external():
    assert gate_text("hello", DataClassification.PUBLIC, provider_is_local=False) == "hello"
