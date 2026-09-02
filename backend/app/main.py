from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_router
from app.api.health import router as health_router
from app.api.jobs import jobs_router
from app.api.planning import planning_router
from app.api.portfolio import portfolio_router
from app.api.settings import settings_router
from app.api.auth import auth_router
from app.api.projects import projects_router
from app.api.tasks import tasks_router
from app.api.ws import ws_router
from app.config import settings
from app.core.redis_client import redis_available
from app.core.security.rate_limit import RateLimitMiddleware

_subscriber_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _subscriber_task
    if settings.arq_enabled and redis_available():
        from app.core.realtime.planning_events import run_planning_subscriber

        _subscriber_task = asyncio.create_task(run_planning_subscriber())
    yield
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Projektmanagement API",
    version="0.7.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
