#!/usr/bin/env bash
# Single-threaded pg_dump, gzip'd, rotated locally. Meant to run via cron on
# the VPS, e.g.:  0 3 * * * /path/to/kort/deploy/backup-db.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

set -a
source .env
set +a

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$DB_USER" -p "$DB_PORT" "$DB_NAME" | gzip > "$BACKUP_DIR/kort-$TIMESTAMP.sql.gz"

find "$BACKUP_DIR" -name "kort-*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete: $BACKUP_DIR/kort-$TIMESTAMP.sql.gz"
