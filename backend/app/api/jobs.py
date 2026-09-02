"""Job-Status API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models import User
from app.services.generation_job_service import JobError, get_job_for_user

jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.get("/{job_id}")
def get_generation_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_job_for_user(db, user, job_id)
    except JobError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=exc.message) from exc
