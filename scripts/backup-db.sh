#!/usr/bin/env bash
# PostgreSQL-Backup des Docker-Volumes (CT 129)
#
# Cron-Beispiel (täglich 03:00):
#   0 3 * * * /opt/projektmanagement/scripts/backup-db.sh >> /var/log/pm-backup.log 2>&1

set -euo pipefail

REPO_DIR="/opt/projektmanagement"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/projektmanagement}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "FEHLER: .env fehlt" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/pm-db-${STAMP}.sql.gz"

echo "==> Backup nach $OUT"
docker compose exec -T db pg_dump -U pm projektmanagement | gzip > "$OUT"

echo "==> Alte Backups (> ${RETENTION_DAYS} Tage) löschen"
find "$BACKUP_DIR" -name 'pm-db-*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete

ls -lh "$OUT"
echo "==> Fertig."
