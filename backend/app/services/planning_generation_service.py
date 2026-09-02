"""KI-Generierung für Planungsschritte (Idee + Schritte 1–6, 9–10)."""

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto.classification import DataClassification
from app.core.llm import generate_text
from app.core.llm.token_cost import build_usage_estimate
from app.core.llm.types import LlmRequest
from app.models import Project, User
from app.services.llm_config_service import get_runtime_config
from app.services.planning_constants import (
    ARTIFACT_LABELS,
    ARTIFACT_ORDER,
    KI_GENERATABLE_ARTIFACTS,
    PROJECT_TYPE_LABELS,
)
from app.services.planning_service import (
    PlanningError,
    ensure_planning_framework,
    get_planning_state,
    save_artifact,
    save_project_idea,
)

PLANNING_SYSTEM_PROMPT = """Du bist ein erfahrener Schweizer Projektmanager (PMP, IPMA Level B).
Erstelle professionelle Planungsdokumente auf Deutsch mit Markdown (##, Tabellen, Listen).
Fakten aus der Projektidee und vorherigen Planungsartefakten haben Vorrang — nichts erfinden.
Schweizer Orthographie (ss, kein ß). Antworte NUR mit dem Dokument — keine Präambel."""

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
    "pflichtenheft": """Erstelle ein **gehaltvolles kurzes Pflichtenheft für das Projektsetup**.
Zweck: Idee in prüfbare Anforderungen übersetzen — keine vollumfängliche Ausschreibung.

Projektidee:
{idea}

{context}

Recherche-Kontext:
{research_context}

{budget_context}

Pflicht-Abschnitte (Markdown):
1. Zweck und Nutzen
2. Was dieses Projekt typischerweise tangiert (Fliesstext, Klärungsfragen)
3. Ausgangslage, Zielbild, In/Out of Scope
4. Stakeholder und Verantwortlichkeiten
5. Funktionale Anforderungen (FA-001 …, 10–18 Stück mit Akzeptanzkriterium)
6. Nichtfunktionale Anforderungen (NFA-001 …)
7. Schnittstellen, Daten, Abhängigkeiten
8. Rahmenbedingungen (Organisation, Betrieb, Compliance)
9. Budget und Kostenrahmen (nur wie in Budget-Kontext vorgegeben)
10. Offene Punkte und nächste Schritte""",
    "netzplan": """Erstelle einen **Netzplan** (Aktivitätenliste mit Abhängigkeiten) für folgendes Projekt.

Projektidee:
{idea}

{context}

Pflicht-Inhalte:
1. Einleitung (Methode)
2. Aktivitätentabelle: ID | Aktivität | Dauer (Tage) | Frühster Start | Frühster Abschluss | Spätester Start | Spätester Abschluss | Puffer | Vorgänger
3. Kritischer Pfad
4. Meilensteine (mind. 5, relativ zu Projektstart)
5. Gesamtprojektdauer in Arbeitstagen

Stütze dich auf den PSP aus den vorherigen Artefakten.""",
    "projektplan": """Erstelle einen **Projektplan (Gantt-Darstellung)** für folgendes Projekt.

Projektidee:
{idea}

{context}

Pflicht-Inhalte:
1. Projektübersicht (Start, Ende, Gesamtdauer)
2. Gantt-Tabelle: AP-ID | Arbeitspaket | Verantwortlich | Start (Woche) | Ende (Woche) | Dauer (Wochen) | Abhängigkeiten | Meilenstein
   — alle Arbeitspakete aus dem PSP, mind. 20 Zeilen
3. Meilensteinplan
4. Ressourcenübersicht nach Wochen
5. Kritische Termine und Eskalationspunkte""",
    "einsatzmittelplan": """Erstelle einen **realistischen Einsatzmittelplan (Ressourcenplan)** für folgendes Projekt.

Projektidee:
{idea}

{context}

Pflicht-Abschnitte (Markdown):
1. Kurzanalyse (Projekttyp, Laufzeit, Meeting-Rhythmus)
2. Rollenübersicht: Rolle | Profil | Verantwortlichkeiten | Gesamt-PT
3. Durchlaufende PM-/Koordinationsleistung (Tabelle)
4. Personalbedarfsmatrix nach Projektphase
5. Ressourcenzuweisung pro Arbeitspaket (AP-ID aus PSP)
6. Externe Ressourcen (nur wenn im Projekt vorgesehen)
7. RACI-Matrix für Hauptphasen
8. Ressourcenauslastung — übernimm die deterministische Tabelle unten UNVERÄNDERT
9. Ressourcenkonflikte und Massnahmen

Alle Rollen und PT müssen zum PSP und Budgetplan passen — nichts erfinden.""",
    "risikobetrachtung": """Erstelle eine vollständige **Risikobetrachtung** (Schritt 10) für folgendes Projekt.

Leite alle Risiken **ausschliesslich** aus den Planungsdokumenten 1–9 ab — nichts erfinden.

Projektidee:
{idea}

{context}

Pflicht-Inhalte:
1. Einleitung (Methodik, Skala 1–5)
2. Risikoregister-Tabelle: ID | Risiko | Kategorie | Ursache | W | A | Score | Massnahme | Verantwortlich | Status
   — mind. 8–12 konkrete Projektrisiken
3. Top-5-Risiken mit Begründung (Quelle: welches Dokument)
4. Risikomatrix (Zusammenfassung)
5. Contingency-Empfehlung (% vom Budget, begründet)
6. Überwachungs- und Eskalationsplan""",
}

_EINSATZMITTEL_SOURCE_SLUGS = ARTIFACT_ORDER[:8]
_RISIKO_SOURCE_SLUGS = ARTIFACT_ORDER[:9]

# Lineare Voraussetzung je KI-Schritt (unmittelbarer Vorgänger in ARTIFACT_ORDER)
_KI_PREREQUISITES: dict[str, str | None] = {
    "zielplanung": None,
    "projektbeschrieb": "zielplanung",
    "psp": "projektbeschrieb",
    "pflichtenheft": "psp",
    "netzplan": "pflichtenheft",
    "projektplan": "netzplan",
    "einsatzmittelplan": "budgetplan",
    "risikobetrachtung": "einsatzmittelplan",
}

_MAX_TOKENS: dict[str, int] = {
    "pflichtenheft": 6500,
    "einsatzmittelplan": 5000,
    "risikobetrachtung": 5000,
}


def _artifact_by_slug(artifacts: list[dict], slug: str) -> dict | None:
    return next((a for a in artifacts if a["slug"] == slug), None)


def _build_previous_context(artifacts: list[dict], up_to_slug: str) -> str:
    parts: list[str] = []
    for slug in ARTIFACT_ORDER:
        if slug == up_to_slug:
            break
        item = _artifact_by_slug(artifacts, slug)
        if item and item.get("has_content") and item.get("content"):
            label = ARTIFACT_LABELS.get(slug, slug)
            parts.append(f"### {label}\n{item['content']}")
    if not parts:
        return ""
    joined = "\n\n---\n\n".join(parts)
    return f"Bereits erstellte Planungsdokumente:\n\n{joined}"


def _budget_context_for_pflichtenheft(artifacts: list[dict]) -> str:
    budget = _artifact_by_slug(artifacts, "budgetplan")
    content = (budget.get("content") or "").strip() if budget else ""
    if content:
        return (
            "### Budgetplan Schritt 8 (verbindlich — Kapitel 9)\n\n"
            f"{content[:10000]}\n"
        )
    return (
        "_Noch kein Budgetplan vorhanden. Kostenrahmen nur qualitativ — "
        "keine erfundenen CHF-Beträge. Hinweis: Zahlen folgen aus Budgetplan (Schritt 8)._"
    )


def _count_filled(artifacts: list[dict], slugs: list[str]) -> int:
    return sum(
        1
        for slug in slugs
        if (item := _artifact_by_slug(artifacts, slug)) and item.get("has_content")
    )


def _require_prerequisite(artifacts: list[dict], slug: str) -> None:
    prereq = _KI_PREREQUISITES.get(slug)
    if prereq:
        item = _artifact_by_slug(artifacts, prereq)
        if not item or not item.get("has_content"):
            label = ARTIFACT_LABELS.get(prereq, prereq)
            raise PlanningError(
                f"Zuerst Schritt «{label}» ausfüllen oder generieren",
                "missing_prerequisite",
            )

    if slug == "einsatzmittelplan" and _count_filled(artifacts, _EINSATZMITTEL_SOURCE_SLUGS) < 2:
        raise PlanningError(
            "Für den Einsatzmittelplan werden mindestens 2 befüllte Planungsschritte 1–8 benötigt",
            "missing_prerequisite",
        )
    if slug == "risikobetrachtung" and _count_filled(artifacts, _RISIKO_SOURCE_SLUGS) < 2:
        raise PlanningError(
            "Für die Risikobetrachtung werden mindestens 2 befüllte Planungsschritte 1–9 benötigt",
            "missing_prerequisite",
        )


def _run_planning_llm(
    config,
    request: LlmRequest,
) -> tuple[str, dict]:
    llm = generate_text(
        config,
        request,
        data_classification=DataClassification.CONFIDENTIAL,
    )
    usage = build_usage_estimate(
        provider=config.provider,
        model=config.model,
        is_local=config.is_local,
        input_tokens=llm.input_tokens,
        output_tokens=llm.output_tokens,
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt,
        response_text=llm.text,
    )
    return llm.text, usage.to_dict()


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
    content, llm_usage = _run_planning_llm(
        config,
        LlmRequest(system_prompt=PLANNING_SYSTEM_PROMPT, user_prompt=prompt, model=config.model),
    )
    result = save_project_idea(
        db, user, project, idea=content, expected_revision=expected_revision
    )
    result["llm_usage"] = llm_usage
    return result


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

    _require_prerequisite(state["artifacts"], slug)

    context = _build_previous_context(state["artifacts"], slug) or "(kein Vorgänger-Inhalt)"
    template = _ARTIFACT_PROMPTS[slug]

    if slug == "pflichtenheft":
        user_prompt = template.format(
            idea=idea,
            context=context,
            research_context=(
                "_Keine externe Recherche — arbeite aus Idee und Planungsartefakten._"
            ),
            budget_context=_budget_context_for_pflichtenheft(state["artifacts"]),
        )
    else:
        user_prompt = template.format(idea=idea, context=context)

    determ_table = ""
    if slug == "einsatzmittelplan":
        psp_item = _artifact_by_slug(state["artifacts"], "psp")
        psp_content = (psp_item.get("content") or "") if psp_item else ""
        try:
            from app.services.resource_utilization_service import build_resource_utilization_table

            determ_table = build_resource_utilization_table(
                psp_content, title=project.key
            )
            user_prompt += (
                "\n\n---\n\n## Deterministisch berechnete Ressourcenauslastung (aus PSP)\n\n"
                "**WICHTIG: Die folgende Tabelle ist KORREKT — in Abschnitt 8 UNVERÄNDERT übernehmen.**\n\n"
                f"{determ_table}"
            )
        except ValueError:
            pass

    config = get_runtime_config(db, user)
    content, llm_usage = _run_planning_llm(
        config,
        LlmRequest(
            system_prompt=PLANNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=config.model,
            max_tokens=_MAX_TOKENS.get(slug, 4096),
        ),
    )

    if slug == "einsatzmittelplan" and determ_table and "Ressourcenauslastung" not in (content or ""):
        content = (content or "").rstrip() + "\n\n---\n\n" + determ_table

    artifact = next(a for a in state["artifacts"] if a["slug"] == slug)
    result = save_artifact(
        db,
        user,
        project,
        slug=slug,
        content=content,
        expected_version=artifact["version"],
    )
    result["llm_usage"] = llm_usage
    return result
