"""KI-Generierung für Planungsschritte (Idee + Schritte 1–3)."""

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto.classification import DataClassification
from app.core.llm import LLMError, generate_text
from app.core.llm.types import LlmRequest
from app.models import Project, User
from app.services.llm_config_service import get_runtime_config
from app.services.planning_constants import KI_GENERATABLE_ARTIFACTS, PROJECT_TYPE_LABELS
from app.services.planning_service import (
    PlanningError,
    ensure_planning_framework,
    get_planning_state,
    save_artifact,
    save_project_idea,
)

PLANNING_SYSTEM_PROMPT = """Du bist ein erfahrener Schweizer Projektmanager (PMP, IPMA Level B).
Erstelle professionelle Planungsdokumente auf Deutsch mit Markdown (##, Tabellen, Listen).
Fakten aus der Projektidee haben Vorrang — nichts erfinden oder widersprechen.
Antworte NUR mit dem Dokument — keine Präambel."""

_ARTIFACT_PROMPTS: dict[str, str] = {
    "zielplanung": """Erstelle eine vollständige **Zielplanung** für folgendes Projekt.

Projektidee:
{idea}

{context}

Abschnitte: Projekttitel, SMART-Ziele, Teilziele (mind. 3), KPIs, Abgrenzung, Randbedingungen, Ziel-Risiken.""",
    "projektbeschrieb": """Erstelle einen **Projektbeschrieb** auf Basis der Projektidee und Zielplanung.

Projektidee:
{idea}

Bisherige Planung:
{context}

Abschnitte: Ausgangslage, Business Case, Deliverables, Scope, Stakeholder, Organisation.""",
    "psp": """Erstelle einen **Projektstrukturplan (PSP)** mit 3 Hierarchieebenen und PT-Spalte (Ganzzahlen).

Projektidee:
{idea}

Bisherige Planung:
{context}

Markdown-Tabelle: AP-ID | Arbeitspaket | Verantwortlich | PT | Beschreibung.""",
}


def _build_context(artifacts: list[dict], before_slug: str | None) -> str:
    if not before_slug:
        return ""
    parts: list[str] = []
    for item in artifacts:
        if item["slug"] == before_slug:
            break
        if item.get("has_content") and item.get("content"):
            parts.append(f"### {item['slug']}\n{item['content']}")
    return "\n\n".join(parts)


def _context_before(slug: str) -> str | None:
    order = ["zielplanung", "projektbeschrieb", "psp"]
    if slug not in order:
        return None
    idx = order.index(slug)
    if idx == 0:
        return None
    return order[idx - 1]


def generate_project_idea(
    db: Session,
    user: User,
    project: Project,
    *,
    seed: str | None,
    expected_revision: int,
) -> dict:
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    state = get_planning_state(db, user, project)
    base = (seed or state["project_idea"] or project.key).strip()
    if not base:
        raise PlanningError("Bitte eine Ausgangslage oder Projektidee angeben", "missing_seed")

    type_label = PROJECT_TYPE_LABELS.get(project.project_type, project.project_type)
    config = get_runtime_config(db, user)
    prompt = f"""Formuliere eine prägnante **Projektidee** (½–1 Seite Markdown) für ein Projekt vom Typ «{type_label}».

Ausgangslage / Stichworte:
{base}

Abschnitte: Vision, Problemstellung, Nutzen, grober Scope."""
    content = generate_text(
        config,
        LlmRequest(system_prompt=PLANNING_SYSTEM_PROMPT, user_prompt=prompt, model=config.model),
        data_classification=DataClassification.CONFIDENTIAL,
    )
    return save_project_idea(
        db, user, project, idea=content, expected_revision=expected_revision
    )


def generate_artifact(
    db: Session,
    user: User,
    project: Project,
    *,
    slug: str,
    expected_revision: int,
) -> dict:
    if slug not in KI_GENERATABLE_ARTIFACTS:
        raise PlanningError("KI-Generierung für dieses Artefakt noch nicht verfügbar", "not_supported")

    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    state = get_planning_state(db, user, project)
    idea = state["project_idea"].strip()
    if not idea:
        raise PlanningError("Zuerst Projektidee erfassen oder generieren", "missing_idea")

    before = _context_before(slug)
    if slug == "projektbeschrieb":
        ziel = next((a for a in state["artifacts"] if a["slug"] == "zielplanung"), None)
        if not ziel or not ziel["has_content"]:
            raise PlanningError("Zuerst Schritt 1 (Zielplanung) ausfüllen oder generieren", "missing_prerequisite")
    if slug == "psp":
        beschr = next((a for a in state["artifacts"] if a["slug"] == "projektbeschrieb"), None)
        if not beschr or not beschr["has_content"]:
            raise PlanningError("Zuerst Schritt 2 (Projektbeschrieb) ausfüllen oder generieren", "missing_prerequisite")

    context = _build_context(state["artifacts"], before)
    template = _ARTIFACT_PROMPTS[slug]
    user_prompt = template.format(idea=idea, context=context or "(kein Vorgänger-Inhalt)")

    config = get_runtime_config(db, user)
    content = generate_text(
        config,
        LlmRequest(system_prompt=PLANNING_SYSTEM_PROMPT, user_prompt=user_prompt, model=config.model),
        data_classification=DataClassification.CONFIDENTIAL,
    )

    artifact = next(a for a in state["artifacts"] if a["slug"] == slug)
    result = save_artifact(
        db,
        user,
        project,
        slug=slug,
        content=content,
        expected_version=artifact["version"],
    )
    return result
