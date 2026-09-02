"""DOCX-Export für Planungsartefakte."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.export.docx import build_docx_bytes
from app.models import Project, User
from app.services.planning_constants import ARTIFACT_LABELS, ARTIFACT_ORDER
from app.services.planning_service import PlanningError, get_planning_state


def export_planning_docx_bytes(db: Session, user: User, project: Project) -> tuple[bytes, str]:
    state = get_planning_state(db, user, project)
    artifact_map = {a["slug"]: a for a in state["artifacts"]}

    sections: list[tuple[str, str]] = [("Projektidee", state.get("project_idea") or "")]
    for slug in ARTIFACT_ORDER:
        art = artifact_map.get(slug)
        sections.append((ARTIFACT_LABELS[slug], art["content"] if art else ""))

    data = build_docx_bytes(
        title="KI-Projektplanungsschritte",
        subtitle_lines=[f"Projekt: {project.key}"],
        sections=sections,
        monospace_labels={ARTIFACT_LABELS["jira_csv"]},
    )
    return data, f"{project.key}_KI-Projektplanungsschritte.docx"


def export_artifact_docx_bytes(
    db: Session,
    user: User,
    project: Project,
    slug: str,
) -> tuple[bytes, str]:
    if slug not in ARTIFACT_ORDER:
        raise PlanningError("Unbekannter Artefakt-Typ", "invalid_slug")

    state = get_planning_state(db, user, project)
    artifact_map = {a["slug"]: a for a in state["artifacts"]}
    art = artifact_map.get(slug)
    content = art["content"] if art else ""
    if not content.strip():
        raise PlanningError("Artefakt hat noch keinen Inhalt", "empty_artifact")

    label = ARTIFACT_LABELS[slug]
    data = build_docx_bytes(
        title=label,
        subtitle_lines=[f"Projekt: {project.key}"],
        sections=[(label, content)],
        monospace_labels={label} if slug == "jira_csv" else set(),
    )
    safe = slug.replace("_", "-")
    return data, f"{project.key}_{safe}.docx"
