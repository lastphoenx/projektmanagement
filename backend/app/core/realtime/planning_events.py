"""Planungs-Live-Events über Redis Pub/Sub + WebSocket."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

PLANNING_CHANNEL = "planning:updates"


class PlanningConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, project_key: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(project_key, set()).add(websocket)

    async def disconnect(self, project_key: str, websocket: WebSocket) -> None:
        async with self._lock:
            room = self._rooms.get(project_key)
            if not room:
                return
            room.discard(websocket)
            if not room:
                self._rooms.pop(project_key, None)

    async def broadcast(self, project_key: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._rooms.get(project_key, ()))
        if not sockets:
            return
        message = json.dumps(payload, separators=(",", ":"))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(project_key, ws)


planning_connections = PlanningConnectionManager()


def publish_planning_update(
    *,
    project_key: str,
    revision: int | None = None,
    source: str,
    job_id: str | None = None,
) -> None:
    client = get_redis()
    if not client:
        return
    payload = {
        "event": "planning_updated",
        "project_key": project_key,
        "revision": revision,
        "source": source,
        "job_id": job_id,
    }
    try:
        client.publish(PLANNING_CHANNEL, json.dumps(payload, separators=(",", ":")))
    except Exception:
        logger.exception("Redis publish failed for planning update")


async def run_planning_subscriber() -> None:
    """Hört Redis-Events und leitet sie an lokale WebSocket-Räume weiter."""
    client = get_redis()
    if not client:
        return
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(PLANNING_CHANNEL)
    while True:
        try:
            message = await asyncio.to_thread(pubsub.get_message, timeout=1.0)
            if not message or message.get("type") != "message":
                await asyncio.sleep(0.05)
                continue
            data = message.get("data")
            if isinstance(data, bytes):
                data = data.decode()
            payload = json.loads(data)
            project_key = payload.get("project_key")
            if project_key:
                await planning_connections.broadcast(project_key, payload)
        except asyncio.CancelledError:
            pubsub.close()
            raise
        except Exception:
            logger.exception("Planning subscriber error")
            await asyncio.sleep(1.0)
