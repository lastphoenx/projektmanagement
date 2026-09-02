#!/usr/bin/env bash
# Auf CT 129: git pull + Docker neu bauen/starten
#
# Erstmalig: siehe doku/pve2/vm/129-projektmanagement/ct129-projektmanagement.md
# Danach bei jedem Update: ./scripts/deploy.sh

set -euo pipefail

REPO_DIR="/opt/projektmanagement"
cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "FEHLER: .env fehlt. Einmalig: cp .env.example .env && nano .env" >&2
  exit 1
fi

if [[ -d .git ]]; then
  echo "==> git pull"
  git pull --ff-only
else
  echo "WARNUNG: kein git-Repo — manueller Stand, kein pull" >&2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/fix-docker-ipv4.sh"

echo "==> Build & start"
export DOCKER_BUILDKIT=1
if [[ "${DOCKER_PRUNE_BUILDER:-1}" == "1" ]]; then
  echo "==> Docker Build-Cache leeren (API-Image mit PyTorch; DOCKER_PRUNE_BUILDER=0 zum Überspringen)"
  docker builder prune -af >/dev/null 2>&1 || true
fi
docker compose build
docker compose up -d

echo "==> DB-Migration"
docker compose exec -T api alembic upgrade head

echo "==> Health (über Frontend-Proxy)"
sleep 3
if ! curl -fsS "http://127.0.0.1:3000/api/v1/health"; then
  echo ""
  echo "==> Container-Logs:"
  docker compose logs --tail 30
  exit 1
fi
echo ""

if [[ "${PII_PREFETCH_ON_DEPLOY:-0}" == "1" ]]; then
  echo "==> PII-Modelle vorladen (Flair; kann einige Minuten dauern)"
  docker compose exec -T api python scripts/prefetch_pii_models.py
fi

echo "==> Fertig."
