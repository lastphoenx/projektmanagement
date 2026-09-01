"""Planungs-API (Projekt-Key-basiert)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.db import get_db
from app.core.llm.errors import LLMError
from app.models import User
from app.schemas import (
    BudgetBasisConfirmRequest,
    BudgetBasisUpdateRequest,
    GenerateArtifactRequest,
    GenerateIdeaRequest,
    PlanningStateResponse,
    SaveArtifactRequest,
    SaveProjectIdeaRequest,
    SetArtifactStatusRequest,
)
from app.services.planning_generation_service import generate_artifact, generate_project_idea
from app.services.psp_budget_service import analyze_psp_budget, confirm_budget_basis, update_budget_basis
from app.services.planning_service import (
    PlanningError,
    get_planning_state,
    save_artifact,
    save_project_idea,
    set_artifact_status,
)
from app.services.project_service import ProjectError, get_project_entity_by_key

planning_router = APIRouter(prefix="/projects/by-key/{project_key}/planning", tags=["planning"])


def _project(db: Session, user: User, project_key: str):
    try:
        return get_project_entity_by_key(db, user, project_key)
    except ProjectError as exc:
        code = status.HTTP_403_FORBIDDEN if exc.code == "forbidden" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


def _planning_http_error(exc: PlanningError | LLMError) -> HTTPException:
    if isinstance(exc, LLMError):
        if exc.code == "not_configured":
            code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif exc.code == "pii_blocked":
            code = status.HTTP_403_FORBIDDEN
        else:
            code = status.HTTP_502_BAD_GATEWAY
        return HTTPException(status_code=code, detail=exc.message)

    if exc.code == "version_conflict":
        code = status.HTTP_409_CONFLICT
    elif exc.code in ("invalid_key", "invalid_type", "invalid_slug", "invalid_status", "missing_prerequisite", "missing_idea", "missing_seed", "not_supported"):
        code = status.HTTP_400_BAD_REQUEST
    elif exc.code == "not_found":
        code = status.HTTP_404_NOT_FOUND
    else:
        code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=exc.message)


@planning_router.get("", response_model=PlanningStateResponse)
def planning_get(
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        return get_planning_state(db, user, project)
    except PlanningError as exc:
        raise _planning_http_error(exc) from exc


@planning_router.put("/idea", response_model=PlanningStateResponse)
def planning_save_idea(
    project_key: str,
    body: SaveProjectIdeaRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = save_project_idea(
            db,
            user,
            project,
            idea=body.idea,
            expected_revision=body.expected_revision,
        )
        db.commit()
        return result
    except PlanningError as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.put("/artifacts/{slug}", response_model=PlanningStateResponse)
def planning_save_artifact(
    project_key: str,
    slug: str,
    body: SaveArtifactRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = save_artifact(
            db,
            user,
            project,
            slug=slug,
            content=body.content,
            expected_version=body.expected_version,
        )
        db.commit()
        return result
    except PlanningError as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.patch("/artifacts/{slug}/status", response_model=PlanningStateResponse)
def planning_set_artifact_status(
    project_key: str,
    slug: str,
    body: SetArtifactStatusRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = set_artifact_status(db, user, project, slug=slug, status=body.status)
        db.commit()
        return result
    except PlanningError as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.post("/generate/idea", response_model=PlanningStateResponse)
def planning_generate_idea(
    project_key: str,
    body: GenerateIdeaRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = generate_project_idea(
            db,
            user,
            project,
            seed=body.seed,
            expected_revision=body.expected_revision,
        )
        db.commit()
        return result
    except (PlanningError, LLMError) as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.post("/generate/artifacts/{slug}", response_model=PlanningStateResponse)
def planning_generate_artifact(
    project_key: str,
    slug: str,
    body: GenerateArtifactRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = generate_artifact(
            db,
            user,
            project,
            slug=slug,
            expected_revision=body.expected_revision,
        )
        db.commit()
        return result
    except (PlanningError, LLMError) as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.get("/psp-analysis")
def planning_psp_analysis(
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        return analyze_psp_budget(db, user, project)
    except PlanningError as exc:
        raise _planning_http_error(exc) from exc


@planning_router.put("/budget-basis")
def planning_budget_basis_update(
    project_key: str,
    body: BudgetBasisUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = update_budget_basis(
            db,
            user,
            project,
            budget_ceiling_chf=body.budget_ceiling_chf,
            notes=body.notes,
            expected_revision=body.expected_revision,
        )
        db.commit()
        return result
    except PlanningError as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc


@planning_router.post("/budget-basis/confirm", response_model=PlanningStateResponse)
def planning_budget_basis_confirm(
    project_key: str,
    body: BudgetBasisConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_key)
    try:
        result = confirm_budget_basis(
            db, user, project, expected_revision=body.expected_revision
        )
        db.commit()
        return result
    except PlanningError as exc:
        db.rollback()
        raise _planning_http_error(exc) from exc
