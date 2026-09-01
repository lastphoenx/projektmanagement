"""SQLAlchemy-Modelle."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base
from app.core.crypto.classification import DataClassification


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Tenant(Base, TimestampMixin):
    """Mandant – vorbereitet für späteres SaaS."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.INTERNAL, nullable=False
    )

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    projects: Mapped[list["Project"]] = relationship(back_populates="tenant")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email_hash_tenant", "tenant_id", "email_hash", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    encryption_salt: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    encrypted_profile: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    totp_secret_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.SECRET, nullable=False
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    recovery_codes: Mapped[list["RecoveryCode"]] = relationship(back_populates="user")


class UserSession(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="recovery_codes")


class LoginChallenge(Base):
    __tablename__ = "login_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_tenant_key", "tenant_id", "key", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(8), nullable=False)
    project_type: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    name_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    description_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.INTERNAL, nullable=False
    )
    version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    locked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project")
    planning_framework: Mapped["PlanningFramework | None"] = relationship(
        back_populates="project", uselist=False
    )


class PlanningFramework(Base, TimestampMixin):
    __tablename__ = "planning_frameworks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    project_idea_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    budget_basis_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    revision: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.CONFIDENTIAL, nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="planning_framework")
    artifacts: Mapped[list["PlanningArtifact"]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )


class PlanningArtifact(Base, TimestampMixin):
    __tablename__ = "planning_artifacts"
    __table_args__ = (Index("ix_planning_artifacts_framework_slug", "framework_id", "slug", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    framework_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("planning_frameworks.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    content_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.CONFIDENTIAL, nullable=False
    )

    framework: Mapped["PlanningFramework"] = relationship(back_populates="artifacts")


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (
        Index("ix_project_members_project_user", "project_id", "user_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="members")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    body_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.INTERNAL, nullable=False
    )
    version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    locked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")


class TenantLlmConfig(Base, TimestampMixin):
    __tablename__ = "tenant_llm_configs"
    __table_args__ = (Index("ix_tenant_llm_configs_tenant_active", "tenant_id", "is_active"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="gpt-4o-mini")
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_key_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.SECRET, nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[int] = mapped_column(
        SmallInteger, default=DataClassification.INTERNAL, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
