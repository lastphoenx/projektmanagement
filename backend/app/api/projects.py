"""Projekt- und Mitglieder-API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.rbac import ProjectRole, get_accessible_project, require_role
from app.core.db import get_db
from app.models import User
from app.schemas import (
    MemberAddRequest,
    MemberResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.member_service import MemberError, add_member, list_members, remove_member
from app.services.project_service import (
    ProjectError,
    create_project,
    delete_project,
    get_project_by_key,
    get_project_for_user,
    list_projects,
    lock_project,
    unlock_project,
    update_project,
)

projects_router = APIRouter(prefix="/projects", tags=["projects"])


def accessible_project(db: Session, user: User, project_id: UUID):
    return get_accessible_project(db, user, project_id)


@projects_router.get("", response_model=list[ProjectResponse])
def projects_list(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_projects(db, user)


@projects_router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def projects_create(
    body: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = create_project(
            db,
            user,
            key=body.key,
            name=body.name,
            project_type=body.project_type,
            description=body.description,
            classification=body.classification,
        )
        db.commit()
        return result
    except ProjectError as exc:
        db.rollback()
        code = status.HTTP_400_BAD_REQUEST
        if exc.code == "key_taken":
            code = status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.get("/by-key/{project_key}", response_model=ProjectResponse)
def projects_get_by_key(
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_project_by_key(db, user, project_key)
    except ProjectError as exc:
        code = status.HTTP_403_FORBIDDEN if exc.code == "forbidden" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def projects_get(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_project_for_user(db, user, project_id)
    except ProjectError as exc:
        code = status.HTTP_403_FORBIDDEN if exc.code == "forbidden" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.patch("/{project_id}", response_model=ProjectResponse)
def projects_update(
    project_id: UUID,
    body: ProjectUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = update_project(
            db,
            user,
            project_id,
            name=body.name,
            description=body.description,
            version=body.version,
        )
        db.commit()
        return result
    except ProjectError as exc:
        db.rollback()
        if exc.code == "version_conflict":
            code = status.HTTP_409_CONFLICT
        elif exc.code in ("forbidden", "locked"):
            code = status.HTTP_403_FORBIDDEN
        else:
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def projects_delete(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        delete_project(db, user, project_id)
        db.commit()
    except ProjectError as exc:
        db.rollback()
        code = status.HTTP_403_FORBIDDEN if exc.code == "forbidden" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.post("/{project_id}/lock", response_model=ProjectResponse)
def projects_lock(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = lock_project(db, user, project_id)
        db.commit()
        return result
    except ProjectError as exc:
        db.rollback()
        code = status.HTTP_423_LOCKED if exc.code == "locked" else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.delete("/{project_id}/lock", response_model=ProjectResponse)
def projects_unlock(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = unlock_project(db, user, project_id)
        db.commit()
        return result
    except ProjectError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@projects_router.get("/{project_id}/members", response_model=list[MemberResponse])
def members_list(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    return list_members(db, project)


@projects_router.post("/{project_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def members_add(
    project_id: UUID,
    body: MemberAddRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    require_role(db, user, project, ProjectRole.MANAGER)
    try:
        result = add_member(
            db,
            user,
            project,
            user_id=UUID(body.user_id),
            role_label=body.role,
        )
        db.commit()
        return result
    except MemberError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@projects_router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def members_remove(
    project_id: UUID,
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    require_role(db, user, project, ProjectRole.MANAGER)
    try:
        remove_member(db, user, project, member_id)
        db.commit()
    except MemberError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
