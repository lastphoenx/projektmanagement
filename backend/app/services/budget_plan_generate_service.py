"""Budgetplan-Artefakt aus PSP erzeugen und speichern."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto import encrypt_text_master
from app.models import PlanningArtifact, Project, User
from app.services.audit import log_event
from app.services.budget_plan_service import build_budgetplan_from_psp
from app.services.planning_constants import ARTIFACT_STATUS_FROM_LABEL, ARTIFACT_STATUS_PENDING
from app.services.planning_service import (
    PlanningError,
    ensure_planning_framework,
    get_planning_state,
)


def _budget_ceiling_from_state(state: dict) -> float | None:
    basis = state.get("budget_basis") or {}
    ceiling = basis.get("budget_ceiling_chf")
    if ceiling is None:
        return None
    try:
        return float(ceiling)
    except (TypeError, ValueError):
        return None


def generate_budgetplan_from_psp(
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
            "Für den Budgetplan (Schritt 8) wird zuerst der Projektstrukturplan (PSP, Schritt 3) benötigt.",
            "missing_psp",
        )

    idea_line = (state.get("project_idea") or "").split("\n")[0].strip()
    try:
        content = build_budgetplan_from_psp(
            psp["content"],
            project_title=idea_line[:120] if idea_line else project.key,
            project_type=project.project_type,
            budget_ceiling_chf=_budget_ceiling_from_state(state),
        )
    except ValueError as exc:
        raise PlanningError(str(exc), "parse_failed") from exc

    artifact = (
        db.query(PlanningArtifact)
        .filter(
            PlanningArtifact.framework_id == framework.id,
            PlanningArtifact.slug == "budgetplan",
        )
        .first()
    )
    if not artifact:
        raise PlanningError("Artefakt budgetplan nicht gefunden", "not_found")

    artifact.content_encrypted = encrypt_text_master(content)
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
        action="planning.budgetplan.generate",
        resource_type="planning_artifact",
        resource_id=artifact.id,
        detail=project.key,
    )
    return get_planning_state(db, user, project)
