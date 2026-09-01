"""Jira-CSV-Artefakt aus PSP erzeugen und speichern."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto import encrypt_text_master
from app.models import PlanningArtifact, Project, User
from app.services.audit import log_event
from app.services.jira_csv_service import build_jira_csv_from_psp
from app.services.planning_constants import ARTIFACT_STATUS_FROM_LABEL, ARTIFACT_STATUS_PENDING
from app.services.planning_service import (
    PlanningError,
    ensure_planning_framework,
    get_planning_state,
)


def generate_jira_csv_from_psp(
    db: Session,
    user: User,
    project: Project,
    *,
    expected_revision: int,
) -> dict:
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    state = get_planning_state(db, user, project)
    psp = next((a for a in state["artifacts"] if a["slug"] == "psp"), None)
    if not psp or not psp["content"].strip():
        raise PlanningError(
            "Für die Jira CSV (Schritt 7) wird zuerst der Projektstrukturplan (PSP, Schritt 3) benötigt.",
            "missing_psp",
        )

    idea_line = (state.get("project_idea") or "").split("\n")[0].strip()
    try:
        csv_content = build_jira_csv_from_psp(
            project.key,
            psp["content"],
            project_title=idea_line[:120] if idea_line else None,
        )
    except ValueError as exc:
        raise PlanningError(str(exc), "parse_failed") from exc

    artifact = (
        db.query(PlanningArtifact)
        .filter(
            PlanningArtifact.framework_id == framework.id,
            PlanningArtifact.slug == "jira_csv",
        )
        .first()
    )
    if not artifact:
        raise PlanningError("Artefakt jira_csv nicht gefunden", "not_found")

    artifact.content_encrypted = encrypt_text_master(csv_content)
    artifact.version += 1
    if artifact.status == ARTIFACT_STATUS_PENDING:
        artifact.status = ARTIFACT_STATUS_FROM_LABEL["draft"]
    artifact.generated_at = datetime.now(timezone.utc)
    framework.revision += 1
    db.flush()

    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="planning.jira_csv.generate",
        resource_type="planning_artifact",
        resource_id=artifact.id,
        detail=project.key,
    )
    return get_planning_state(db, user, project)
