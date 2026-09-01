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

# Viele Homelab-CTs haben IPv6-Adressen, aber keinen IPv6-Default-Route.
# Docker Hub (CloudFront) wird dann per v6 angesprochen → "network is unreachable".
ensure_docker_registry_ipv4() {
  if [[ ! -f /proc/sys/net/ipv6/conf/all/disable_ipv6 ]]; then
    return 0
  fi
  if ping6 -c1 -W2 2600:9000:: >/dev/null 2>&1; then
    return 0
  fi
  echo "==> IPv6-Upstream nicht erreichbar — deaktiviere IPv6 für Docker-Pulls (diese Session)"
  sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null 2>&1 || true
  sysctl -w net.ipv6.conf.default.disable_ipv6=1 >/dev/null 2>&1 || true
}

ensure_docker_registry_ipv4

echo "==> Build & start"
export DOCKER_BUILDKIT=1
docker compose build
docker compose up -d

echo "==> Health (über Frontend-Proxy)"
sleep 3
if ! curl -fsS "http://127.0.0.1:3000/api/v1/health"; then
  echo ""
  echo "==> Container-Logs:"
  docker compose logs --tail 30
  exit 1
fi
echo ""

echo "==> Fertig."
