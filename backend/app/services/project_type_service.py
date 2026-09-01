"""Projekttyp → PT-Sätze (CHF/PT) für Budgetauswertung."""

from app.services.planning_constants import ProjectType

# Wizard-Typ → Budget-Logik (ein Typ-System)
TYPE_RATES: dict[str, dict[str, float]] = {
    ProjectType.NEW_PRODUCT: {"default": 1000, "pm": 1200, "dev": 1000, "test": 800, "reserve_pct": 0.12},
    ProjectType.PROCESS_IMPROVEMENT: {"default": 950, "pm": 1150, "dev": 950, "test": 750, "reserve_pct": 0.10},
    ProjectType.INFRASTRUCTURE: {"default": 900, "pm": 1150, "dev": 950, "test": 750, "reserve_pct": 0.10},
    ProjectType.OTHER: {"default": 950, "pm": 1200, "dev": 1000, "test": 800, "reserve_pct": 0.12},
}


def rates_for_project_type(project_type: str) -> dict[str, float]:
    return TYPE_RATES.get(project_type, TYPE_RATES[ProjectType.OTHER])


def role_rate_key(responsible: str) -> str:
    r = (responsible or "").lower()
    if any(x in r for x in ("test", "qa", "qualität")):
        return "test"
    if any(x in r for x in ("pm", "projekt", "leitung", "management")):
        return "pm"
    if any(x in r for x in ("dev", "entwick", "architect", "engineer")):
        return "dev"
    return "default"
