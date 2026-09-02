"""Verschlüsselte Portfolio-Felder — Master-Key, analog zu Project.name_encrypted."""

from __future__ import annotations

import json
from typing import Any

from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.models import PortfolioProject

FINANCIAL_KEYS = ("financial_npv", "financial_roi_pct", "payback_months", "cost_total")


def _encrypt_optional(text: str | None) -> bytes | None:
    if text is None or text == "":
        return None
    return encrypt_text_master(text)


def _decrypt_optional(blob: bytes | None) -> str | None:
    if not blob:
        return None
    return decrypt_text_master(blob)


def portfolio_name(entry: PortfolioProject) -> str:
    return _decrypt_optional(entry.name_encrypted) or ""


def portfolio_sponsor(entry: PortfolioProject) -> str | None:
    return _decrypt_optional(entry.sponsor_encrypted)


def portfolio_objective(entry: PortfolioProject, index: int) -> str | None:
    blob = (
        entry.objective_1_encrypted
        if index == 1
        else entry.objective_2_encrypted
        if index == 2
        else entry.objective_3_encrypted
    )
    return _decrypt_optional(blob)


def read_financial(entry: PortfolioProject) -> dict[str, int]:
    if not entry.financial_encrypted:
        return {key: 0 for key in FINANCIAL_KEYS}
    data = json.loads(decrypt_text_master(entry.financial_encrypted))
    return {key: int(data.get(key, 0)) for key in FINANCIAL_KEYS}


def write_financial(
    entry: PortfolioProject,
    *,
    financial_npv: int,
    financial_roi_pct: int,
    payback_months: int,
    cost_total: int,
) -> None:
    entry.financial_encrypted = encrypt_text_master(
        json.dumps(
            {
                "financial_npv": financial_npv,
                "financial_roi_pct": financial_roi_pct,
                "payback_months": payback_months,
                "cost_total": cost_total,
            },
            separators=(",", ":"),
        )
    )


def apply_sensitive_fields(entry: PortfolioProject, data: dict[str, Any]) -> None:
    """Schreibt verschlüsselte Stammdaten aus API-Dict (Klartext)."""
    if "name" in data and data["name"] is not None:
        entry.name_encrypted = encrypt_text_master(str(data["name"]))
    if "sponsor" in data:
        entry.sponsor_encrypted = _encrypt_optional(data.get("sponsor"))
    if "objective_1" in data:
        entry.objective_1_encrypted = _encrypt_optional(data.get("objective_1"))
    if "objective_2" in data:
        entry.objective_2_encrypted = _encrypt_optional(data.get("objective_2"))
    if "objective_3" in data:
        entry.objective_3_encrypted = _encrypt_optional(data.get("objective_3"))

    financial_keys = {k for k in FINANCIAL_KEYS if k in data and data[k] is not None}
    if financial_keys:
        current = read_financial(entry)
        for key in FINANCIAL_KEYS:
            if key in data and data[key] is not None:
                current[key] = int(data[key])
        write_financial(entry, **current)


def sensitive_fields_to_dict(entry: PortfolioProject) -> dict[str, Any]:
    """Entschlüsselt für API-Antworten."""
    fin = read_financial(entry)
    return {
        "name": portfolio_name(entry),
        "sponsor": portfolio_sponsor(entry),
        "objective_1": portfolio_objective(entry, 1),
        "objective_2": portfolio_objective(entry, 2),
        "objective_3": portfolio_objective(entry, 3),
        **fin,
    }
