"""Tests für Token-Schätzung und API-Preistabelle."""

from app.core.llm.token_cost import (
    BILLING_NOTE,
    build_usage_estimate,
    calculate_cost_usd,
    estimate_tokens,
    pricing_catalog_for_ui,
    pricing_for_model,
)


def test_estimate_tokens_heuristic():
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_pricing_for_model_prefix_match():
    assert pricing_for_model("claude-haiku-4-5-20251001") is not None
    assert pricing_for_model("gpt-4.1-mini") == (0.40, 1.60)


def test_calculate_cost_usd():
    cost = calculate_cost_usd("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost == 0.15 + 0.60


def test_build_usage_estimate_local():
    est = build_usage_estimate(
        provider="ollama",
        model="llama3.3:70b",
        is_local=True,
        input_tokens=1000,
        output_tokens=500,
        system_prompt="sys",
        user_prompt="user",
        response_text="out",
    )
    d = est.to_dict()
    assert d["is_local"] is True
    assert d["estimated_cost_usd"] is None
    assert d["total_tokens"] == 1500


def test_build_usage_estimate_cloud_fallback_tokens():
    est = build_usage_estimate(
        provider="openai",
        model="gpt-4.1-mini",
        is_local=False,
        input_tokens=None,
        output_tokens=None,
        system_prompt="a" * 400,
        user_prompt="b" * 400,
        response_text="c" * 400,
    )
    assert est.input_tokens == 200
    assert est.output_tokens == 100
    assert est.cost_usd is not None


def test_pricing_catalog_for_ui():
    rows = pricing_catalog_for_ui()
    assert any(r["model"] == "gpt-4.1-mini" for r in rows)
    assert all("example_idea_usd" in r for r in rows)


def test_billing_note_mentions_plus_and_pro():
    text = " ".join(BILLING_NOTE["paragraphs"])
    assert "Plus" in text
    assert "Pro" in text
    assert "API" in text
