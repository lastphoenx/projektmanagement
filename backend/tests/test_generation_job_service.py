"""Tests für ARQ-Generation-Jobs."""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth.passwords import hash_email, hash_password
from app.core.crypto.classification import DataClassification
from app.core.db.session import Base
from app.models import GenerationJob, Project, Tenant, User
from app.services.generation_job_service import JobError, create_planning_job, get_job_for_user


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    import app.models  # noqa: F401

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _seed_project(db):
    tenant = Tenant(slug="test-tenant")
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email_hash=hash_email("user@example.com"),
        password_hash=hash_password("testpassword123456"),
        encryption_salt=os.urandom(32),
        classification=DataClassification.SECRET,
    )
    db.add(user)
    db.flush()
    project = Project(
        tenant_id=tenant.id,
        created_by_id=user.id,
        key="TST01",
        project_type="software",
        name_encrypted=b"name",
        classification=DataClassification.INTERNAL,
    )
    db.add(project)
    db.commit()
    return user, project


def test_create_and_fetch_generation_job(db_session):
    user, project = _seed_project(db_session)
    job = create_planning_job(
        db_session,
        user,
        project,
        kind="planning_idea",
        artifact_slug=None,
        payload={"expected_revision": 1},
    )
    db_session.commit()

    data = get_job_for_user(db_session, user, job.id)
    assert data["status"] == "pending"
    assert data["kind"] == "planning_idea"
    assert data["project_key"] == "TST01"
    assert data["planning"] is None


def test_get_job_for_user_not_found(db_session):
    user, _ = _seed_project(db_session)
    with pytest.raises(JobError) as exc:
        get_job_for_user(db_session, user, uuid.uuid4())
    assert exc.value.code == "not_found"


def test_get_job_for_user_wrong_owner(db_session):
    user, project = _seed_project(db_session)
    other = User(
        tenant_id=user.tenant_id,
        email_hash=hash_email("other@example.com"),
        password_hash=hash_password("testpassword123456"),
        encryption_salt=os.urandom(32),
        classification=DataClassification.SECRET,
    )
    db_session.add(other)
    db_session.flush()
    job = GenerationJob(
        tenant_id=user.tenant_id,
        user_id=user.id,
        project_id=project.id,
        project_key=project.key,
        kind="planning_idea",
        status="pending",
    )
    db_session.add(job)
    db_session.commit()

    with pytest.raises(JobError):
        get_job_for_user(db_session, other, job.id)
