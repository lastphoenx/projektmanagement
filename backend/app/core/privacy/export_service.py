"""DSGVO Art. 15 — Auskunft über personenbezogene Daten."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.crypto.classification_catalog import get_policy
from app.core.crypto.field_registry import gdpr_fields_for_model
from app.models import AuditLog, Project, ProjectMember, User, UserLlmPreference, UserSession


class PrivacyError(Exception):
    def __init__(self, message: str, code: str = "privacy_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def export_user_data(db: Session, user_id: uuid.UUID) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise PrivacyError("Benutzer nicht gefunden", "not_found")

    memberships = (
        db.query(ProjectMember, Project)
        .join(Project, ProjectMember.project_id == Project.id)
        .filter(ProjectMember.user_id == user.id)
        .all()
    )

    audit_events = (
        db.query(AuditLog)
        .filter(AuditLog.actor_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(500)
        .all()
    )

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .order_by(UserSession.created_at.desc())
        .limit(50)
        .all()
    )

    llm_pref = db.get(UserLlmPreference, user.id)

    gdpr_field_manifest = [
        {
            "model": f.model,
            "field": f.field,
            "classification": f.classification.name,
            "gdpr_personal": f.gdpr_personal,
        }
        for f in gdpr_fields_for_model("User")
    ]

    secret_policy = get_policy(user.classification)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "legal_basis": "DSGVO Art. 15 — Auskunft",
        "subject_user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "account": {
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "totp_enabled": user.totp_enabled,
            "classification": secret_policy.label,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        "personal_data_fields": gdpr_field_manifest,
        "stored_identifiers": {
            "email_hash": user.email_hash,
            "note": "E-Mail ist nur als HMAC-Hash gespeichert; Klartext nicht rekonstruierbar.",
        },
        "encrypted_profile": {
            "present": user.encrypted_profile is not None,
            "exportable": secret_policy.exportable,
            "note": "Profil (z.B. Anzeigename) ist mit Benutzerpasswort verschlüsselt — nur der Nutzer kann entschlüsseln.",
        },
        "project_memberships": [
            {
                "project_id": str(project.id),
                "project_key": project.key,
                "role": member.role,
                "since": member.created_at.isoformat(),
            }
            for member, project in memberships
        ],
        "sessions": [
            {
                "id": str(s.id),
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
            }
            for s in sessions
        ],
        "llm_preference": (
            {
                "provider": llm_pref.provider,
                "model": llm_pref.model,
                "updated_at": llm_pref.updated_at.isoformat(),
            }
            if llm_pref
            else None
        ),
        "login_challenges_note": (
            "Aktive Login-Challenges werden nicht exportiert (kurzlebig, max. wenige Minuten)."
        ),
        "audit_events": [
            {
                "id": str(e.id),
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": str(e.resource_id) if e.resource_id else None,
                "detail": e.detail,
                "created_at": e.created_at.isoformat(),
            }
            for e in audit_events
        ],
    }
