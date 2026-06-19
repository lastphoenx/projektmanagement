from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import config
from app.core.auth.dependencies import get_challenge_token, get_current_user
from app.core.auth.rbac import ProjectRole, get_accessible_project, require_role
from app.core.auth.sessions import (
    clear_challenge_cookie,
    clear_session_cookie,
    create_session,
    revoke_session,
    set_challenge_cookie,
    set_session_cookie,
)
from app.core.db import get_db
from app.models import User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    MemberAddRequest,
    MemberResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    RegisterRequest,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
    TwoFactorConfirmRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserResponse,
)
from app.services.member_service import MemberError, add_member, list_members, remove_member
from app.services.project_service import (
    ProjectError,
    create_project,
    delete_project,
    get_project_for_user,
    list_projects,
    lock_project,
    unlock_project,
    update_project,
)
from app.services.task_service import TaskError, create_task, delete_task, get_task, list_tasks, lock_task, unlock_task, update_task
from app.services.user_service import (
    AuthError,
    authenticate_password,
    complete_2fa_login,
    confirm_totp,
    register_user,
    setup_totp,
    start_2fa_challenge,
    user_public_dict,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
projects_router = APIRouter(prefix="/projects", tags=["projects"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(**user_public_dict(user))


def _finish_login(db: Session, user: User, response: Response) -> LoginResponse:
    token, _ = create_session(db, user.id)
    db.commit()
    set_session_cookie(response, token)
    clear_challenge_cookie(response)
    return LoginResponse(user=_user_response(user))


def _project(db: Session, user: User, project_id: UUID):
    return get_accessible_project(db, user, project_id)


# ── Auth ──────────────────────────────────────────────────────────────────────


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not config.settings.allow_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registrierung deaktiviert")
    try:
        user = register_user(
            db,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
        )
        db.commit()
        return _user_response(user)
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@auth_router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = authenticate_password(db, body.email, body.password)
        if user.totp_enabled:
            challenge = start_2fa_challenge(db, user)
            db.commit()
            set_challenge_cookie(response, challenge)
            return LoginResponse(requires_2fa=True)
        return _finish_login(db, user, response)
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@auth_router.post("/2fa/verify", response_model=LoginResponse)
def verify_2fa(
    body: TwoFactorVerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
    challenge_token: str = Depends(get_challenge_token),
):
    if not body.totp_code and not body.recovery_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code erforderlich")
    try:
        user = complete_2fa_login(
            db,
            challenge_token,
            totp_code=body.totp_code,
            recovery_code=body.recovery_code,
        )
        return _finish_login(db, user, response)
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=config.settings.cookie_name),
):
    if session_token:
        revoke_session(db, session_token)
    clear_session_cookie(response)
    clear_challenge_cookie(response)
    db.commit()


@auth_router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return _user_response(user)


@auth_router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def totp_setup(
    body: LoginRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        secret, uri = setup_totp(db, user, body.email)
        db.commit()
        return TwoFactorSetupResponse(provisioning_uri=uri, secret=secret)
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@auth_router.post("/2fa/confirm")
def totp_confirm(
    body: TwoFactorConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        codes = confirm_totp(db, user, body.code, body.email)
        db.commit()
        return {"recovery_codes": codes}
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


# ── Projects ──────────────────────────────────────────────────────────────────


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
            name=body.name,
            description=body.description,
            classification=body.classification,
        )
        db.commit()
        return result
    except ProjectError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


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


# ── Members ───────────────────────────────────────────────────────────────────


@projects_router.get("/{project_id}/members", response_model=list[MemberResponse])
def members_list(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    return list_members(db, project)


@projects_router.post("/{project_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def members_add(
    project_id: UUID,
    body: MemberAddRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
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
    project = _project(db, user, project_id)
    require_role(db, user, project, ProjectRole.MANAGER)
    try:
        remove_member(db, user, project, member_id)
        db.commit()
    except MemberError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


# ── Tasks ─────────────────────────────────────────────────────────────────────


@projects_router.get("/{project_id}/tasks", response_model=list[TaskResponse])
def tasks_list(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    return list_tasks(db, project)


@projects_router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def tasks_create(
    project_id: UUID,
    body: TaskCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
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


@projects_router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def tasks_get(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    require_role(db, user, project, ProjectRole.VIEWER)
    try:
        return get_task(db, project, task_id)
    except TaskError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@projects_router.patch("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def tasks_update(
    project_id: UUID,
    task_id: UUID,
    body: TaskUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
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


@projects_router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def tasks_delete(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    try:
        delete_task(db, user, project, task_id)
        db.commit()
    except TaskError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc


@projects_router.post("/{project_id}/tasks/{task_id}/lock", response_model=TaskResponse)
def tasks_lock(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    try:
        result = lock_task(db, user, project, task_id)
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        code = status.HTTP_423_LOCKED if exc.code == "locked" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=exc.message) from exc


@projects_router.delete("/{project_id}/tasks/{task_id}/lock", response_model=TaskResponse)
def tasks_unlock(
    project_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project(db, user, project_id)
    try:
        result = unlock_task(db, user, project, task_id)
        db.commit()
        return result
    except TaskError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
