#!/usr/bin/env bash
# CT ohne IPv6-Default-Route: Docker Hub per v6 → "network is unreachable".
# Einmalig oder vor deploy.sh — idempotent.
set -euo pipefail

GAI_MARKER="# projektmanagement: prefer-ipv4"

ipv6_default_route() {
  ip -6 route show default 2>/dev/null | grep -q .
}

ipv6_registry_reachable() {
  command -v ping6 >/dev/null 2>&1 && ping6 -c1 -W3 registry-1.docker.io >/dev/null 2>&1
}

needs_ipv4_fix() {
  if ! ipv6_default_route; then
    return 0
  fi
  if ! ipv6_registry_reachable; then
    return 0
  fi
  return 1
}

apply_gai_prefer_ipv4() {
  if grep -qF "$GAI_MARKER" /etc/gai.conf 2>/dev/null; then
    return 0
  fi
  printf '\n%s\nprecedence ::ffff:0:0/96  100\n' "$GAI_MARKER" >>/etc/gai.conf
  echo "==> /etc/gai.conf: IPv4 bevorzugt"
}

disable_ipv6_sysctl() {
  echo "==> IPv6 per sysctl deaktivieren"
  sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null
  sysctl -w net.ipv6.conf.default.disable_ipv6=1 >/dev/null
  for f in /proc/sys/net/ipv6/conf/*/disable_ipv6; do
    echo 1 >"$f" 2>/dev/null || true
  done
  mkdir -p /etc/sysctl.d
  cat >/etc/sysctl.d/99-projektmanagement-disable-ipv6.conf <<'EOF'
# CT ohne IPv6-Upstream — Docker Registry sonst unreachable
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
}

ensure_docker_daemon_no_ipv6() {
  mkdir -p /etc/docker
  local changed
  changed="$(python3 <<'PY'
import json
from pathlib import Path

p = Path("/etc/docker/daemon.json")
data: dict = {}
if p.exists():
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        data = {}
if data.get("ipv6") is False:
    print("0")
else:
    data["ipv6"] = False
    p.write_text(json.dumps(data, indent=2) + "\n")
    print("1")
PY
)"
  if [[ "$changed" == "1" ]]; then
    echo "==> /etc/docker/daemon.json: \"ipv6\": false"
    echo "==> Docker neu starten …"
    systemctl restart docker
    sleep 3
  fi
}

main() {
  if ! needs_ipv4_fix; then
    echo "==> IPv6-Upstream erreichbar — kein Registry-Fix nötig"
    return 0
  fi
  echo "==> Kein nutzbarer IPv6-Upstream — erzwinge IPv4 für Docker"
  apply_gai_prefer_ipv4
  disable_ipv6_sysctl
  ensure_docker_daemon_no_ipv6
  echo "==> Registry-Fix angewendet"
}

main "$@"
