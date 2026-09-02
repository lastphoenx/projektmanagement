# Hintergrund-Jobs mit ARQ

**Status:** implementiert (Migration `010`, Redis + Worker in `docker-compose.yml`).

## Problem

KI-Generierung in der Planung kann 30s–2min dauern. Synchron im API-Prozess blockiert Requests und riskiert Timeouts.

## Architektur

```
POST /planning/generate/...  →  Job in Redis  →  202 { job_id }
ARQ Worker                   →  LLM + Speichern →  Job status: done
GET  /jobs/{id}              →  Polling (Frontend wartet automatisch)
WebSocket /ws/planning/{key} →  Live-Reload bei Speichern/Job-Ende
```

## Komponenten

| Teil | Ort |
|------|-----|
| Redis | `docker-compose.yml` → `redis:6379` |
| Worker | `docker compose` Service `worker` → `arq app.worker.WorkerSettings` |
| Jobs-Tabelle | `generation_jobs` (Alembic `010`) |
| API | `POST generate/*` → 202 wenn Redis erreichbar, sonst Sync-Fallback |
| Status | `GET /api/v1/jobs/{job_id}` |
| Realtime | Redis Pub/Sub `planning:updates` + WebSocket |

## Konfiguration (`.env`)

```env
REDIS_URL=redis://redis:6379/0
ARQ_ENABLED=true
```

Ohne Redis: API fällt auf synchronen Modus zurück (`arq_jobs_enabled()` → false).

## Produktion (nginx)

WebSocket braucht direkten Proxy zum API-Port — Next.js unterstützt kein WS-Upgrade. Siehe `doku/.../pm.santinel.li.conf` → `location /api/v1/ws/`.

## Multi-User

Jeder Job speichert `user_id`. Der Worker nutzt `build_runtime_config(db, user)` — PII-Gate bleibt aktiv.
