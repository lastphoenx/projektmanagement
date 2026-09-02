"""WebSocket — Live-Planungsupdates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth.sessions import get_valid_session
from app.core.db.session import SessionLocal
from app.core.realtime.planning_events import planning_connections
from app.models import User
from app.services.project_service import ProjectError, get_project_entity_by_key

ws_router = APIRouter(tags=["websocket"])


def _user_from_cookie(db: Session, token: str | None) -> User | None:
    session = get_valid_session(db, token or "")
    if not session:
        return None
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        return None
    return user


@ws_router.websocket("/ws/planning/{project_key}")
async def planning_websocket(websocket: WebSocket, project_key: str):
    db = SessionLocal()
    try:
        user = _user_from_cookie(db, websocket.cookies.get(settings.cookie_name))
        if not user:
            await websocket.close(code=4401)
            return
        try:
            get_project_entity_by_key(db, user, project_key)
        except ProjectError as exc:
            close_code = 4403 if exc.code == "forbidden" else 4404
            await websocket.close(code=close_code)
            return
        await planning_connections.connect(project_key, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await planning_connections.disconnect(project_key, websocket)
    finally:
        db.close()
