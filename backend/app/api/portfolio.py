"""Portfolio-API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models import User
from app.schemas.portfolio import (
    PortfolioEligibleProjectResponse,
    PortfolioProjectCreateRequest,
    PortfolioProjectResponse,
    PortfolioProjectUpdateRequest,
)
from app.services.portfolio_service import (
    PortfolioError,
    create_portfolio_entry,
    delete_portfolio_entry,
    get_matrix_data,
    get_portfolio_by_project_key,
    get_portfolio_entry,
    get_wsjf_ranking,
    list_eligible_projects,
    list_portfolio_entries,
    update_portfolio_entry,
)
from app.services.project_service import ProjectError, get_project_entity_by_key
portfolio_router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _http_error(exc: PortfolioError | ProjectError) -> HTTPException:
    if exc.code == "not_found":
        code = status.HTTP_404_NOT_FOUND
    elif exc.code in ("forbidden",):
        code = status.HTTP_403_FORBIDDEN
    elif exc.code in ("planning_incomplete", "already_exists"):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=exc.message)


@portfolio_router.get("/projects", response_model=list[PortfolioProjectResponse])
def portfolio_list(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_portfolio_entries(db, user)


@portfolio_router.get("/eligible-projects", response_model=list[PortfolioEligibleProjectResponse])
def portfolio_eligible(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_eligible_projects(db, user)


@portfolio_router.get("/matrix-data")
def portfolio_matrix(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_matrix_data(db, user)


@portfolio_router.get("/wsjf-ranking")
def portfolio_wsjf(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_wsjf_ranking(db, user)


@portfolio_router.get("/by-project-key/{project_key}", response_model=PortfolioProjectResponse | None)
def portfolio_by_key(
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_portfolio_by_project_key(db, user, project_key)
    except ProjectError as exc:
        raise _http_error(exc) from exc


@portfolio_router.get("/projects/{entry_id}", response_model=PortfolioProjectResponse)
def portfolio_get(
    entry_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_portfolio_entry(db, user, entry_id)
    except PortfolioError as exc:
        raise _http_error(exc) from exc


@portfolio_router.post("/projects", response_model=PortfolioProjectResponse, status_code=status.HTTP_201_CREATED)
def portfolio_create(
    body: PortfolioProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = body.model_dump()
        project_key = data.pop("project_key")
        result = create_portfolio_entry(db, user, project_key=project_key, data=data)
        db.commit()
        return result
    except (PortfolioError, ProjectError) as exc:
        db.rollback()
        raise _http_error(exc) from exc


@portfolio_router.put("/projects/{entry_id}", response_model=PortfolioProjectResponse)
def portfolio_update(
    entry_id: uuid.UUID,
    body: PortfolioProjectUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = update_portfolio_entry(
            db, user, entry_id, body.model_dump(exclude_unset=True)
        )
        db.commit()
        return result
    except PortfolioError as exc:
        db.rollback()
        raise _http_error(exc) from exc


@portfolio_router.delete("/projects/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def portfolio_delete(
    entry_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        delete_portfolio_entry(db, user, entry_id)
        db.commit()
    except PortfolioError as exc:
        db.rollback()
        raise _http_error(exc) from exc
