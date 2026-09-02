"""Auth-API: Registrierung, Login, 2FA, Session."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app import config
from app.core.auth.dependencies import get_challenge_token, get_current_user
from app.core.auth.sessions import (
    clear_challenge_cookie,
    clear_session_cookie,
    create_session,
    revoke_session,
    set_challenge_cookie,
    set_session_cookie,
)
from app.core.db import get_db
from app.core.security.login_protection import (
    check_login_allowed,
    get_client_ip,
    record_login_failure,
    record_login_success,
)
from app.models import User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TwoFactorConfirmRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserResponse,
)
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


def _user_response(user: User) -> UserResponse:
    return UserResponse(**user_public_dict(user))


def _finish_login(db: Session, user: User, response: Response, request: Request) -> LoginResponse:
    token, _ = create_session(db, user.id)
    db.commit()
    set_session_cookie(response, token, request=request)
    clear_challenge_cookie(response, request=request)
    return LoginResponse(user=_user_response(user))


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
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    blocked = check_login_allowed(ip, body.email)
    if blocked:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=blocked)
    try:
        user = authenticate_password(db, body.email, body.password)
        record_login_success(body.email)
        if user.totp_enabled:
            challenge = start_2fa_challenge(db, user)
            db.commit()
            set_challenge_cookie(response, challenge, request=request)
            return LoginResponse(requires_2fa=True)
        return _finish_login(db, user, response, request)
    except AuthError as exc:
        record_login_failure(ip, body.email)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@auth_router.post("/2fa/verify", response_model=LoginResponse)
def verify_2fa(
    body: TwoFactorVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    challenge_token: str = Depends(get_challenge_token),
):
    if not body.totp_code and not body.recovery_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code erforderlich")
    ip = get_client_ip(request)
    blocked = check_login_allowed(ip, "2fa-verify")
    if blocked:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=blocked)
    try:
        user = complete_2fa_login(
            db,
            challenge_token,
            totp_code=body.totp_code,
            recovery_code=body.recovery_code,
        )
        record_login_success("2fa-verify")
        return _finish_login(db, user, response, request)
    except AuthError as exc:
        record_login_failure(ip, "2fa-verify")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=config.settings.cookie_name),
):
    if session_token:
        revoke_session(db, session_token)
    clear_session_cookie(response, request=request)
    clear_challenge_cookie(response, request=request)
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
