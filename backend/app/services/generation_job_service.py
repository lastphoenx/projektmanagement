"""ARQ-Job-Erstellung, Ausführung und Abfrage."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.core.llm.errors import LLMError
from app.core.realtime.planning_events import publish_planning_update
from app.core.redis_client import redis_available
from app.models import GenerationJob, Project, User
from app.services.planning_generation_service import generate_artifact, generate_project_idea
from app.services.planning_service import PlanningError


class JobError(Exception):
    def __init__(self, message: str, code: str = "job_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def arq_jobs_enabled() -> bool:
    return settings.arq_enabled and redis_available()


def _job_to_dict(job: GenerationJob) -> dict[str, Any]:
    result: dict[str, Any] | None = None
    if job.result_payload:
        try:
            result = json.loads(job.result_payload)
        except json.JSONDecodeError:
            result = None
    return {
        "job_id": str(job.id),
        "status": job.status,
        "kind": job.kind,
        "project_key": job.project_key,
        "artifact_slug": job.artifact_slug,
        "error_message": job.error_message,
        "planning": result,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


def get_job_for_user(db: Session, user: User, job_id: uuid.UUID) -> dict[str, Any]:
    job = db.get(GenerationJob, job_id)
    if not job or job.user_id != user.id:
        raise JobError("Job nicht gefunden", "not_found")
    return _job_to_dict(job)


def create_planning_job(
    db: Session,
    user: User,
    project: Project,
    *,
    kind: str,
    artifact_slug: str | None,
    payload: dict[str, Any],
) -> GenerationJob:
    job = GenerationJob(
        tenant_id=user.tenant_id,
        user_id=user.id,
        project_id=project.id,
        project_key=project.key,
        kind=kind,
        artifact_slug=artifact_slug,
        status="pending",
        input_payload=json.dumps(payload, separators=(",", ":")),
    )
    db.add(job)
    db.flush()
    return job


async def enqueue_planning_job(job_id: uuid.UUID) -> None:
    from arq import create_pool
    from arq.connections import RedisSettings

    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_planning_generation_job", str(job_id))


def run_generation_job_sync(job_id: uuid.UUID) -> None:
    from app.core.db.session import SessionLocal

    db = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job or job.status not in ("pending", "running"):
            return
        user = db.get(User, job.user_id)
        project = db.get(Project, job.project_id)
        if not user or not project:
            job.status = "failed"
            job.error_message = "Benutzer oder Projekt nicht gefunden"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        job.status = "running"
        db.commit()

        try:
            payload = json.loads(job.input_payload or "{}")
            if job.kind == "planning_idea":
                result = generate_project_idea(
                    db,
                    user,
                    project,
                    seed=payload.get("seed"),
                    expected_revision=int(payload["expected_revision"]),
                )
            elif job.kind == "planning_artifact":
                result = generate_artifact(
                    db,
                    user,
                    project,
                    slug=job.artifact_slug or payload.get("slug", ""),
                    expected_revision=int(payload["expected_revision"]),
                )
            else:
                raise JobError(f"Unbekannter Job-Typ: {job.kind}", "invalid_kind")

            db.commit()
            job.status = "done"
            job.result_payload = json.dumps(result, default=str)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            publish_planning_update(
                project_key=job.project_key,
                revision=result.get("revision"),
                source="job",
                job_id=str(job.id),
            )
        except (PlanningError, LLMError, JobError) as exc:
            db.rollback()
            job.status = "failed"
            job.error_message = getattr(exc, "message", str(exc))
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
