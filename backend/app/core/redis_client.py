"""Redis-Verbindung für ARQ und Realtime-Pub/Sub."""

from __future__ import annotations

import redis

from app.config import settings

_pool: redis.ConnectionPool | None = None


def get_redis() -> redis.Redis | None:
    if not settings.redis_url:
        return None
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
    return redis.Redis(connection_pool=_pool)


def redis_available() -> bool:
    client = get_redis()
    if not client:
        return False
    try:
        client.ping()
        return True
    except redis.RedisError:
        return False
