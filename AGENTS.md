# Projektmanagement — Hinweise für KI-Assistenten

## Versions-Wahrheit (nicht aus Gedächtnis)

| Was | Kanonische Quelle auf `main` |
|-----|------------------------------|
| Backend-Pins | `backend/requirements.txt` |
| Frontend | `frontend/package.json`, `frontend/package-lock.json` |
| Container-Basis | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |

Install-/Betriebsdoku: **keine Versionsnummern erfinden** — Dateien auf `main` lesen oder nach Deploy auf CT 129 den Stand nach `git pull` annehmen. Privates Detail: `doku/pve2/vm/129-projektmanagement/`.

## Deploy nach Dependency-Änderung auf `main`

**Pflicht**, sonst sind GitHub-Updates wirkungslos:

```bash
# Auf CT 129 (Betreiber)
cd /opt/projektmanagement
DEPLOY_TARGET=api ./scripts/deploy.sh    # nur requirements/Dockerfile Backend
# oder ./scripts/deploy.sh                # inkl. Frontend-Build
```

## Dependabot

- **Security-PRs:** Repo-Einstellung «Dependabot security updates» aktiv (GitHub UI) — CVE-getrieben, unabhängig vom Wochenplan.
- **Version-PRs:** `.github/dependabot.yml` — weekly, **gruppiert** (ein PR pro Backend/Frontend), **keine semver-major** per Config (geplante Majors manuell).
- Obsolete Bot-PRs nach manuellem Bump auf `main`: `scripts/close-dependabot-prs.ps1`.

## Git

Normalerweise **`main`**. Commit/Push nur auf Nutzeranweisung. Deploy führt der Nutzer auf CT 129 aus (kein Agent-SSH).
