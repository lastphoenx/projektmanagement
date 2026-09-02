"""Tests für KI-Hilfetexte und Provider-Metadaten."""

from app.core.llm.guidance import GUIDANCE
from app.core.llm.provider_catalog import PROVIDERS


def test_guidance_covers_all_providers():
    catalog_ids = set(PROVIDERS)
    guidance_ids = {p["id"] for p in GUIDANCE["providers"]}
    assert catalog_ids == guidance_ids


def test_guidance_privacy_rules():
    rules = GUIDANCE["privacy"]["rules"]
    assert any("SECRET" in r for r in rules)
    assert any("anonymisiert" in r.lower() for r in rules)
    assert any("Ollama" in r or "lokal" in r.lower() for r in rules)
