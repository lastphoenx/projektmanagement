"""Integrationstests für DSGVO-Löschung."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth.passwords import hash_email, hash_password
from app.core.crypto.classification import DataClassification
from app.core.db.session import Base
from app.core.privacy.erasure_service import erase_user_data
from app.models import LoginChallenge, Tenant, User, UserLlmPreference


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    import app.models  # noqa: F401 — Tabellen registrieren

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _make_user(
    db,
    tenant: Tenant,
    *,
    email: str,
    is_admin: bool = False,
) -> User:
    user = User(
        tenant_id=tenant.id,
        email_hash=hash_email(email),
        password_hash=hash_password("testpassword123456"),
        encryption_salt=os.urandom(32),
        is_admin=is_admin,
        classification=DataClassification.SECRET,
    )
    db.add(user)
    db.flush()
    return user


def test_erase_user_data_deletes_login_challenges_and_llm_preferences(db_session):
    tenant = Tenant(slug="test-tenant")
    db_session.add(tenant)
    db_session.flush()

    target = _make_user(db_session, tenant, email="target@example.com")
    other = _make_user(db_session, tenant, email="other@example.com")
    actor = _make_user(db_session, tenant, email="admin@example.com", is_admin=True)

    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    db_session.add(
        LoginChallenge(
            user_id=target.id,
            token_hash="target-challenge-hash",
            expires_at=expires,
        )
    )
    db_session.add(
        LoginChallenge(
            user_id=other.id,
            token_hash="other-challenge-hash",
            expires_at=expires,
        )
    )
    db_session.add(
        UserLlmPreference(
            user_id=target.id,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
        )
    )
    db_session.commit()

    result = erase_user_data(db_session, actor, target.id)
    db_session.commit()

    assert result["erased_user_id"] == str(target.id)
    assert (
        db_session.query(LoginChallenge)
        .filter(LoginChallenge.user_id == target.id)
        .count()
        == 0
    )
    assert (
        db_session.query(UserLlmPreference)
        .filter(UserLlmPreference.user_id == target.id)
        .count()
        == 0
    )
    # Fremder Nutzer bleibt unberührt
    assert (
        db_session.query(LoginChallenge)
        .filter(LoginChallenge.user_id == other.id)
        .count()
        == 1
    )

    refreshed = db_session.get(User, target.id)
    assert refreshed is not None
    assert refreshed.is_active is False
