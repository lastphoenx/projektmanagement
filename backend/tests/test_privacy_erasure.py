"""Tests für DSGVO-Löschung — erweiterte Tabellen."""

from pathlib import Path


def test_erasure_service_deletes_login_challenges_and_llm_preferences():
    source = Path(__file__).resolve().parents[1] / "app" / "core" / "privacy" / "erasure_service.py"
    text = source.read_text(encoding="utf-8")
    assert "LoginChallenge" in text
    assert "UserLlmPreference" in text
    assert "LoginChallenge.user_id == user.id" in text
    assert "UserLlmPreference.user_id == user.id" in text
