# Projektmanagement

Self-hosted Projektmanagement mit Python/FastAPI-Backend und Next.js-Frontend.

**Foundation (Phase 1–3)** als Vorlage für neue Secure-Apps: [FOUNDATION.md](FOUNDATION.md) · `./scripts/scaffold-new-app.sh <slug>`

## Architektur

```
projektmanagement/
├── backend/          # FastAPI – Business-Logik, Crypto, Auth, DB
│   └── app/
│       ├── core/     # crypto, auth, db (wiederverwendbar)
│       ├── models/   # SQLAlchemy-Modelle
│       └── api/      # REST-Endpunkte
└── frontend/         # Next.js – nur UI
```

## Voraussetzungen

- Docker & Docker Compose
- Optional lokal: Python 3.12+, Node.js 20+

## Schnellstart

```bash
cp .env.example .env
# ENCRYPTION_MASTER_KEY und SESSION_SECRET in .env setzen (siehe Kommentare)

docker compose up -d db
cd backend && pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (separates Terminal):

```bash
cd frontend && npm install && npm run dev
```

Oder alles per Docker:

```bash
docker compose up -d
```

**UI-Leitplanken:** [frontend/DESIGN.md](frontend/DESIGN.md)

## Datenklassifizierung

| Klasse | Wert | Verschlüsselung |
|--------|------|-----------------|
| PUBLIC | 0 | Keine |
| INTERNAL | 1 | Master-Key (.env) |
| CONFIDENTIAL | 2 | Master-Key (.env) |
| SECRET | 3 | Passwort-abgeleiteter User-Key |

## Phase 4 (aktuell)

- [x] Projekt-Key + Projekttyp (Wizard: Typ → Details → Fertig)
- [x] Planungskern: Idee + 10 Artefakte (PostgreSQL, verschlüsselt)
- [x] Planungs-UI: Sidebar, Markdown-Editor, Vorschau, Status
- [x] Klassifizierungs-Katalog + Feld-Registry (Code-Mapping, B.1)
- [x] KI für Idee + Schritte 1–3 (sync — `core/llm/` + `core/anonymization/pii_gate.py`)
- [x] Admin-UI: KI-Einstellungen (`/admin/llm`), Sicherheitskatalog (`/admin/security`), DSGVO (`/admin/privacy`)
- [x] PSP-Budgetauswertung Schritt 3
- [x] Jira-CSV + Budgetplan aus PSP (Schritte 7–8, Generierung in Planung)
- [x] DOCX-Export (Gesamtplanung + einzelne Artefakte)
- [x] Portfolio-MVP (`/portfolio`, WSJF-Matrix, CRUD)
- [x] API-Router aufgeteilt (`auth`, `projects`, `tasks`, `planning`, `portfolio`, `admin`)
- [ ] Hintergrund-Jobs für lange KI-Generierung (Celery/ARQ o. ä. — siehe unten)
- [ ] WebSocket Live-Updates (optional, Phase 4+)

### Planungs-API (Auszug)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/api/v1/projects/by-key/{key}` | Projekt per Key |
| GET | `/api/v1/projects/by-key/{key}/planning` | Planungsstand |
| PUT | `.../planning/idea` | Projektidee speichern |
| PUT | `.../planning/artifacts/{slug}` | Artefakt speichern |
| PATCH | `.../planning/artifacts/{slug}/status` | Status setzen |
| POST | `.../planning/generate/idea` | KI Projektidee |
| POST | `.../planning/generate/artifacts/{slug}` | KI Artefakt |
| POST | `.../planning/pii-analyze` | PII-Vorschau vor Cloud-Versand |
| GET | `.../planning/export-docx` | Gesamtplanung als DOCX |
| POST | `.../planning/generate/jira-csv` | Jira-CSV aus PSP |
| POST | `.../planning/generate/budgetplan` | Budgetplan aus PSP |

Migration: `cd backend && alembic upgrade head`

### Hintergrund-Jobs (geplant)

Lange KI-Läufe laufen heute **synchron** im API-Worker (ein Request blockiert bis fertig). Für mehrere gleichzeitige Nutzer: Job-Queue (z. B. **Celery** + Redis, oder leichter **ARQ** / **RQ**) mit Status-Polling oder WebSocket — noch nicht implementiert.

## Phase 3

- [x] Tasks CRUD (verschlüsselt, Status: open / in_progress / done)
- [x] RBAC – Rollen viewer, member, manager, owner
- [x] Soft-Locking (15 min Lease) für Projekt- und Task-Bearbeitung
- [x] Projekt-Mitglieder verwalten
- [ ] WebSocket Live-Updates (Phase 4+)

### Rollen

| Rolle | Lesen | Tasks anlegen | Tasks bearbeiten | Projekt bearbeiten | Mitglieder |
|-------|-------|---------------|------------------|--------------------|------------|
| viewer | ✓ | | | | |
| member | ✓ | ✓ | ✓ (mit Lock) | | |
| manager | ✓ | ✓ | ✓ | ✓ (mit Lock) | ✓ |
| owner | ✓ | ✓ | ✓ | ✓ | ✓ |

Tenant-Admins (`is_admin`) haben Owner-Rechte auf alle Projekte.

### Migration

```bash
cd backend && alembic upgrade head   # inkl. 003_rbac_tasks
```

### Neue API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET/POST | `/api/v1/projects/{id}/tasks` | Tasks |
| PATCH/DELETE | `/api/v1/projects/{id}/tasks/{tid}` | Task bearbeiten/löschen |
| POST/DELETE | `/api/v1/projects/{id}/tasks/{tid}/lock` | Task sperren/freigeben |
| POST/DELETE | `/api/v1/projects/{id}/lock` | Projekt sperren/freigeben |
| GET/POST/DELETE | `/api/v1/projects/{id}/members` | RBAC-Mitglieder |

## Phase 2

- [x] Login / Logout mit HttpOnly-Session-Cookie
- [x] 2FA (TOTP) + Recovery Codes
- [x] Bootstrap-Admin-Script
- [x] Projekt-CRUD (verschlüsselt)

## Phase 1

- [x] Projektstruktur & Docker
- [x] PostgreSQL-Schema mit `classification`-Feldern
- [x] `core/crypto` – Argon2id, PBKDF2 (600k), AES-256-GCM
- [x] `core/auth` – Passwort-Hashing, Key-Derivation

## Schlüssel erzeugen

```bash
python -c "import secrets,base64; print('ENCRYPTION_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(64))"
```

## Tests

```bash
cd backend && pytest -v
```

## Produktion (CT 129)

Vollständige Anleitung im `doku`-Repo: `pve2/vm/129-projektmanagement/`

| Aufgabe | Befehl / Ort |
|---------|----------------|
| Deploy / Update | `./scripts/deploy.sh` |
| Docker IPv4-Fix (CT ohne IPv6) | `./scripts/fix-docker-ipv4.sh` (als root; auch via `deploy.sh`) |
| DB-Backup | `./scripts/backup-db.sh` |
| nginx | CT 108 → `pm.santinel.li.conf` |
| 2FA | `2fa-einrichtung.md` |

### Produktions-`.env` (hinter TLS)

```env
CORS_ORIGINS=https://pm.santinel.li
COOKIE_SECURE=true
```

Dann: `docker compose restart api`

