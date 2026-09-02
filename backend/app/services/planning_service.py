"""Planungskern — Framework + Artefakte."""

import json
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.models import PlanningArtifact, PlanningFramework, Project, User
from app.services.planning_constants import (
    ARTIFACT_ORDER,
    ARTIFACT_STATUS_FROM_LABEL,
    ARTIFACT_STATUS_LABELS,
    ARTIFACT_STATUS_PENDING,
    PLANNING_ARTIFACT_SLUGS,
    PROJECT_KEY_PATTERN,
    PROJECT_TYPE_LABELS,
)
from app.services.audit import log_event

PROJECT_KEY_RE = re.compile(PROJECT_KEY_PATTERN)


class PlanningError(Exception):
    def __init__(self, message: str, code: str = "planning_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def normalize_project_key(key: str) -> str:
    return key.strip().upper()


def validate_project_key(key: str) -> None:
    normalized = normalize_project_key(key)
    if not PROJECT_KEY_RE.match(normalized):
        raise PlanningError(
            "Projekt-Key: 2–8 Zeichen, beginnt mit Buchstabe, nur A–Z und 0–9",
            "invalid_key",
        )


def validate_project_type(project_type: str) -> None:
    if project_type not in PROJECT_TYPE_LABELS:
        raise PlanningError("Unbekannter Projekttyp", "invalid_type")


def ensure_planning_framework(db: Session, project: Project) -> PlanningFramework:
    framework = (
        db.query(PlanningFramework).filter(PlanningFramework.project_id == project.id).first()
    )
    if framework:
        return framework

    framework = PlanningFramework(project_id=project.id, revision=1)
    db.add(framework)
    db.flush()

    for slug in ARTIFACT_ORDER:
        db.add(PlanningArtifact(framework_id=framework.id, slug=slug, status=ARTIFACT_STATUS_PENDING))
    db.flush()
    return framework


def _decrypt_optional(blob: bytes | None) -> str:
    if not blob:
        return ""
    return decrypt_text_master(blob)


def _artifact_dict(artifact: PlanningArtifact) -> dict:
    content = _decrypt_optional(artifact.content_encrypted)
    return {
        "slug": artifact.slug,
        "status": ARTIFACT_STATUS_LABELS.get(artifact.status, "pending"),
        "content": content,
        "version": artifact.version,
        "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
        "has_content": bool(content.strip()),
    }


def _completion_stats(project_idea: str, artifacts: list[PlanningArtifact]) -> dict:
    from app.services.planning_completion_service import assess_planning_completion

    artifact_dicts = [_artifact_dict(a) for a in artifacts]
    return assess_planning_completion(project_idea, artifact_dicts)


def get_planning_state(db: Session, user: User, project: Project) -> dict:
    require_role(db, user, project, ProjectRole.VIEWER)
    framework = ensure_planning_framework(db, project)
    artifacts = (
        db.query(PlanningArtifact)
        .filter(PlanningArtifact.framework_id == framework.id)
        .all()
    )
    artifact_by_slug = {a.slug: a for a in artifacts}
    ordered_artifacts = [
        _artifact_dict(artifact_by_slug[slug]) for slug in ARTIFACT_ORDER if slug in artifact_by_slug
    ]
    project_idea = _decrypt_optional(framework.project_idea_encrypted)
    budget_basis_raw = _decrypt_optional(framework.budget_basis_encrypted)
    try:
        budget_basis = json.loads(budget_basis_raw) if budget_basis_raw else {}
    except json.JSONDecodeError:
        budget_basis = {}

    completion = _completion_stats(project_idea, artifacts)
    return {
        "project_key": project.key,
        "revision": framework.revision,
        "project_idea": project_idea,
        "budget_basis": budget_basis,
        "artifacts": ordered_artifacts,
        "completion": completion,
    }


def save_project_idea(
    db: Session,
    user: User,
    project: Project,
    *,
    idea: str,
    expected_revision: int,
) -> dict:
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    framework.project_idea_encrypted = encrypt_text_master(idea) if idea else None
    framework.revision += 1
    db.flush()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="planning.idea.save",
        resource_type="planning_framework",
        resource_id=framework.id,
    )
    return get_planning_state(db, user, project)


def save_artifact(
    db: Session,
    user: User,
    project: Project,
    *,
    slug: str,
    content: str,
    expected_version: int,
) -> dict:
    if slug not in PLANNING_ARTIFACT_SLUGS:
        raise PlanningError("Unbekanntes Artefakt", "invalid_slug")
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    artifact = (
        db.query(PlanningArtifact)
        .filter(PlanningArtifact.framework_id == framework.id, PlanningArtifact.slug == slug)
        .first()
    )
    if not artifact:
        raise PlanningError("Artefakt nicht gefunden", "not_found")
    if artifact.version != expected_version:
        raise PlanningError("Konflikt – Artefakt wurde zwischenzeitlich geändert", "version_conflict")

    artifact.content_encrypted = encrypt_text_master(content) if content else None
    artifact.version += 1
    if content.strip() and artifact.status == ARTIFACT_STATUS_PENDING:
        artifact.status = ARTIFACT_STATUS_FROM_LABEL["draft"]
    artifact.generated_at = datetime.now(timezone.utc)
    framework.revision += 1
    db.flush()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="planning.artifact.save",
        resource_type="planning_artifact",
        resource_id=artifact.id,
        detail=slug,
    )
    return get_planning_state(db, user, project)


def set_artifact_status(
    db: Session,
    user: User,
    project: Project,
    *,
    slug: str,
    status: str,
) -> dict:
    if slug not in PLANNING_ARTIFACT_SLUGS:
        raise PlanningError("Unbekanntes Artefakt", "invalid_slug")
    if status not in ARTIFACT_STATUS_FROM_LABEL:
        raise PlanningError("Ungültiger Status", "invalid_status")
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    artifact = (
        db.query(PlanningArtifact)
        .filter(PlanningArtifact.framework_id == framework.id, PlanningArtifact.slug == slug)
        .first()
    )
    if not artifact:
        raise PlanningError("Artefakt nicht gefunden", "not_found")

    artifact.status = ARTIFACT_STATUS_FROM_LABEL[status]
    framework.revision += 1
    db.flush()
    return get_planning_state(db, user, project)
