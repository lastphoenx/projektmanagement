# Hintergrund-Jobs mit ARQ (Entscheid)

**Status:** geplant — noch nicht implementiert.

## Problem

KI-Generierung in der Planung läuft heute **synchron** im API-Prozess. Bei mehreren Benutzern blockieren sich Requests; lange Läufe (30s–2min) führen zu Timeouts und schlechter UX.

## Entscheid

**ARQ** (async Redis queue) statt Celery:

- leichtgewichtig, passt zu FastAPI/async
- Redis als Broker (ein zusätzlicher Container in `docker-compose.yml`)
- Worker als separater Prozess/Container

## Ziel-Architektur

```
POST /planning/generate/...  →  Job in Redis  →  202 { job_id }
ARQ Worker                   →  LLM + Speichern →  Job status: done
GET  /jobs/{id}              →  polling / später WebSocket
```

## Umsetzungsschritte (Backlog)

1. `redis` Service in `docker-compose.yml`
2. `arq` in `requirements.txt`, Worker-Entrypoint `python -m app.worker`
3. Tabelle `generation_jobs` (status, user_id, project_id, slug, error)
4. Planungs-Endpunkte auf async Job umstellen
5. Frontend: Spinner + Status-Polling auf Planungsseite

## Multi-User

Jeder Benutzer behält eigene KI-Wahl (`user_llm_preferences`). Der Worker liest die User-ID aus dem Job und nutzt `build_runtime_config(db, user)` — PII-Gate bleibt unverändert aktiv.
