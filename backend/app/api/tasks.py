"""Task-API (projektbezogen)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.projects import accessible_project
from app.core.auth.dependencies import get_current_user
from app.core.auth.rbac import ProjectRole, require_role
from app.core.db import get_db
from app.models import User
from app.schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.services.task_service import (
    TaskError,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    lock_task,
    unlock_task,
    update_task,
)

tasks_router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@tasks_router.get("", response_model=list[TaskResponse])
def tasks_list(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    return list_tasks(db, project)


@tasks_router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def tasks_create(
    project_id: UUID,
    body: TaskCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    try:
        result = create_task(
            db,
            user,
            project,
            title=body.title,
            body=body.body,
            status=body.status,
            classification=body.classification,
        )
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def tasks_get(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    try:
        return get_task(db, project, task_id)
    except TaskError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@tasks_router.patch("/{task_id}", response_model=TaskResponse)
def tasks_update(
    project_id: UUID,
    task_id: UUID,
    body: TaskUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    try:
        result = update_task(
            db,
            user,
            project,
            task_id,
            title=body.title,
            body=body.body,
            status=body.status,
            version=body.version,
        )
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        if exc.code == "version_conflict":
            code = status.HTTP_409_CONFLICT
        elif exc.code == "locked":
            code = status.HTTP_423_LOCKED
        else:
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def tasks_delete(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    try:
        delete_task(db, user, project, task_id)
        db.commit()
    except TaskError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc


@tasks_router.post("/{task_id}/lock", response_model=TaskResponse)
def tasks_lock(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    try:
        result = lock_task(db, user, project, task_id)
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        code = status.HTTP_423_LOCKED if exc.code == "locked" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@tasks_router.delete("/{task_id}/lock", response_model=TaskResponse)
def tasks_unlock(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = accessible_project(db, user, project_id)
    try:
        result = unlock_task(db, user, project, task_id)
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
