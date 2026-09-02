"""DSGVO Art. 17 — Löschung / Pseudonymisierung."""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.auth.passwords import hash_email, hash_password
from app.core.crypto.classification_catalog import get_policy
from app.core.crypto.classification import DataClassification
from app.models import AuditLog, LoginChallenge, ProjectMember, RecoveryCode, User, UserLlmPreference, UserSession
from app.services.audit import log_event


class ErasureError(Exception):
    def __init__(self, message: str, code: str = "erasure_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def erase_user_data(db: Session, actor: User, target_user_id: uuid.UUID) -> dict:
    if actor.id == target_user_id and actor.is_admin:
        raise ErasureError("Admin kann sich nicht selbst über diesen Endpunkt löschen", "self_erase")

    user = db.get(User, target_user_id)
    if not user:
        raise ErasureError("Benutzer nicht gefunden", "not_found")
    if user.tenant_id != actor.tenant_id:
        raise ErasureError("Benutzer nicht im gleichen Mandanten", "forbidden")

    policy = get_policy(user.classification)
    if policy.erasure_strategy not in ("delete", "pseudonymize"):
        raise ErasureError("Löschstrategie für diese Klasse nicht unterstützt", "strategy")

    erased_id = user.id

    # Sessions beenden
    db.query(UserSession).filter(UserSession.user_id == user.id).delete(synchronize_session=False)

    # Recovery-Codes entfernen
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user.id).delete(synchronize_session=False)

    # 2FA-Challenges entfernen
    db.query(LoginChallenge).filter(LoginChallenge.user_id == user.id).delete(synchronize_session=False)

    # KI-Präferenzen entfernen
    db.query(UserLlmPreference).filter(UserLlmPreference.user_id == user.id).delete(
        synchronize_session=False
    )

    # Projekt-Mitgliedschaften entfernen
    db.query(ProjectMember).filter(ProjectMember.user_id == user.id).delete(synchronize_session=False)

    # Audit-Log pseudonymisieren (append-only bleibt)
    audit_rows = db.query(AuditLog).filter(AuditLog.actor_id == user.id).all()
    for row in audit_rows:
        row.actor_id = None
        if row.detail:
            row.detail = f"[erased-user:{str(erased_id)[:8]}] {row.detail}"[:2000]
        else:
            row.detail = f"[erased-user:{str(erased_id)[:8]}]"

    # Konto deaktivieren und personenbezogene Felder löschen
    user.is_active = False
    user.totp_enabled = False
    user.totp_secret_encrypted = None
    user.encrypted_profile = None
    user.email_hash = hash_email(f"erased-{secrets.token_hex(16)}@invalid.local")
    user.password_hash = hash_password(secrets.token_hex(32))
    user.classification = DataClassification.INTERNAL

    log_event(
        db,
        tenant_id=actor.tenant_id,
        actor_id=actor.id,
        action="privacy.erase_user",
        resource_type="user",
        resource_id=erased_id,
        detail=f"erased_by={actor.id}",
    )

    return {
        "erased_user_id": str(erased_id),
        "strategy": policy.erasure_strategy,
        "audit_events_pseudonymized": len(audit_rows),
    }
