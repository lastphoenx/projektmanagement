"""ARQ Worker — Planungs-KI im Hintergrund."""

from __future__ import annotations

import asyncio
import uuid

from arq.connections import RedisSettings

from app.config import settings
from app.services.generation_job_service import run_generation_job_sync


async def run_planning_generation_job(ctx, job_id: str) -> None:
    await asyncio.to_thread(run_generation_job_sync, uuid.UUID(job_id))


class WorkerSettings:
    functions = [run_planning_generation_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 2
    job_timeout = 600
