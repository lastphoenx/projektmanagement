#!/usr/bin/env bash
# Schnelles Deploy: nur Code aus Volume-Mounts (api/worker) + Migration.
# Kein Docker-Build — typisch < 30 Sekunden.
#
# Voraussetzung: backend/app ist per Volume gemountet (docker-compose.yml).
# Frontend-Änderungen brauchen: DEPLOY_TARGET=frontend ./scripts/deploy.sh

set -euo pipefail

REPO_DIR="/opt/projektmanagement"
cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "FEHLER: .env fehlt." >&2
  exit 1
fi

if [[ -d .git ]]; then
  echo "==> git pull"
  git pull --ff-only
fi

echo "==> Container starten (neue Services aus compose, ohne Build)"
docker compose up -d --no-build

echo "==> DB-Migration"
docker compose exec -T api alembic upgrade head

echo "==> API + Worker neu laden"
docker compose restart api worker

echo "==> Health"
sleep 2
curl -fsS "http://127.0.0.1:3000/api/v1/health" && echo ""
echo "==> Fertig (quick)."
