"""Retention-Purge gemäss Klassifizierungs-Katalog (B.1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.crypto.classification import DataClassification
from app.core.crypto.classification_catalog import CLASSIFICATION_CATALOG
from app.models import AuditLog, UserSession


def purge_expired_data(db: Session) -> dict[str, int]:
    """Löscht abgelaufene Sessions und alte Audit-Einträge je nach Retention."""
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {"sessions": 0, "audit_log": 0}

    session_cutoff = now - timedelta(days=90)
    counts["sessions"] = (
        db.query(UserSession)
        .filter(UserSession.expires_at < session_cutoff)
        .delete(synchronize_session=False)
    )

    for level, policy in CLASSIFICATION_CATALOG.items():
        if policy.retention_days is None:
            continue
        cutoff = now - timedelta(days=policy.retention_days)
        deleted = (
            db.query(AuditLog)
            .filter(
                AuditLog.classification == level.value,
                AuditLog.created_at < cutoff,
            )
            .delete(synchronize_session=False)
        )
        counts["audit_log"] += deleted

    return counts
