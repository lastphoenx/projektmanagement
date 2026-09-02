"""API-Preise (USD pro 1M Token) und Kostenschätzung — Stand 2026, ohne Gewähr."""

from __future__ import annotations

from dataclasses import dataclass

# input_usd_per_mtok, output_usd_per_mtok — Pay-as-you-go API (nicht Plus/Pro-Abo)
MODEL_PRICING_USD: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4o": (2.50, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-4-20250514": (3.00, 15.00),
}

# Grobe Planungs-Benchmarks (Token) für Vorschau in den Einstellungen
TYPICAL_PLANNING_TOKENS: dict[str, dict[str, int]] = {
    "project_idea": {"input": 1_500, "output": 900},
    "artifact_short": {"input": 4_000, "output": 2_000},
    "artifact_long": {"input": 12_000, "output": 4_500},
}

BILLING_NOTE = {
    "title": "ChatGPT Plus & Claude Pro vs. Server-API",
    "paragraphs": [
        "ChatGPT Plus und Claude Pro sind Abos für die Web-Oberflächen (chat.openai.com, claude.ai). "
        "Sie decken die Nutzung in dieser App nicht ab.",
        "Die Planungs-KI verwendet API-Keys aus der Server-.env (OpenAI Platform / Anthropic Console) "
        "und wird dort separat nach Token abgerechnet — unabhängig von Plus/Pro.",
        "Ollama (lokal) verursacht keine API-Kosten; nur Strom/Hardware auf dem Ollama-Host.",
    ],
    "products": [
        {
            "name": "ChatGPT Plus",
            "covers": "ChatGPT-Web/Apps, begrenzte GPT-4o-Nutzung in der UI",
            "not_covers": "API-Aufrufe aus pm.santinel.li",
        },
        {
            "name": "Claude Pro",
            "covers": "claude.ai Web, höhere Nutzungslimits in der UI",
            "not_covers": "API-Aufrufe aus pm.santinel.li",
        },
    ],
}


@dataclass(frozen=True, slots=True)
class TokenCostEstimate:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float | None  # None = lokal / unbekanntes Modell
    is_local: bool

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.cost_usd, 6) if self.cost_usd is not None else None,
            "estimated_cost_usd_display": (
                f"${self.cost_usd:.4f}" if self.cost_usd is not None else None
            ),
            "is_local": self.is_local,
            "billing_scope": "api_payg" if not self.is_local else "local",
        }


def estimate_tokens(*texts: str) -> int:
    """Heuristik ~4 Zeichen/Token (ohne tiktoken-Abhängigkeit)."""
    total_chars = sum(len(t) for t in texts if t)
    return max(1, total_chars // 4)


def pricing_for_model(model: str) -> tuple[float, float] | None:
    lower = model.lower()
    if lower in MODEL_PRICING_USD:
        return MODEL_PRICING_USD[lower]
    for key, prices in MODEL_PRICING_USD.items():
        if lower.startswith(key) or key in lower:
            return prices
    return None


def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    prices = pricing_for_model(model)
    if not prices:
        return None
    inp_rate, out_rate = prices
    return (input_tokens / 1_000_000) * inp_rate + (output_tokens / 1_000_000) * out_rate


def build_usage_estimate(
    *,
    provider: str,
    model: str,
    is_local: bool,
    input_tokens: int | None,
    output_tokens: int | None,
    system_prompt: str,
    user_prompt: str,
    response_text: str,
) -> TokenCostEstimate:
    inp = input_tokens if input_tokens is not None else estimate_tokens(system_prompt, user_prompt)
    out = output_tokens if output_tokens is not None else estimate_tokens(response_text)
    cost = None if is_local else calculate_cost_usd(model, inp, out)
    return TokenCostEstimate(
        provider=provider,
        model=model,
        input_tokens=inp,
        output_tokens=out,
        total_tokens=inp + out,
        cost_usd=cost,
        is_local=is_local,
    )


def pricing_catalog_for_ui() -> list[dict]:
    rows = []
    for model, (inp, out) in sorted(MODEL_PRICING_USD.items()):
        rows.append(
            {
                "model": model,
                "input_usd_per_mtok": inp,
                "output_usd_per_mtok": out,
                "example_idea_usd": round(
                    calculate_cost_usd(
                        model,
                        TYPICAL_PLANNING_TOKENS["project_idea"]["input"],
                        TYPICAL_PLANNING_TOKENS["project_idea"]["output"],
                    )
                    or 0,
                    4,
                ),
            }
        )
    return rows
