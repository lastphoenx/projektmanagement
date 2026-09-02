#!/usr/bin/env bash
# Auf CT 129: git pull + Docker neu bauen/starten
#
# Modi (DEPLOY_TARGET):
#   all      — alles bauen (Default bei requirements/Dockerfile-Änderungen)
#   api      — nur api + worker (Python-Dependencies / Backend-Image)
#   frontend — nur Next.js-Image
#   restart  — kein Build, nur up + restart api/worker (Volume-Code)
#
# Schnellweg für reine backend/app-Änderungen: ./scripts/deploy-quick.sh
#
# Erstmalig: siehe doku/pve2/vm/129-projektmanagement/ct129-projektmanagement.md

set -euo pipefail

REPO_DIR="/opt/projektmanagement"
cd "$REPO_DIR"

DEPLOY_TARGET="${DEPLOY_TARGET:-all}"

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

echo "==> Deploy-Modus: $DEPLOY_TARGET"
export DOCKER_BUILDKIT=1

if [[ "${DOCKER_PRUNE_BUILDER:-0}" == "1" ]]; then
  echo "==> Docker Build-Cache leeren (nur bei Speicherproblemen nötig)"
  docker builder prune -af >/dev/null 2>&1 || true
fi

case "$DEPLOY_TARGET" in
  all)
    docker compose build
    docker compose up -d
    ;;
  api)
    docker compose build api worker
    docker compose up -d api worker redis
    ;;
  frontend)
    docker compose build frontend
    docker compose up -d frontend
    ;;
  restart)
    docker compose up -d --no-build
    docker compose restart api worker
    ;;
  *)
    echo "FEHLER: unbekannter DEPLOY_TARGET=$DEPLOY_TARGET (all|api|frontend|restart)" >&2
    exit 1
    ;;
esac

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
