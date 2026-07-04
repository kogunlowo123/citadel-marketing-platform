#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="$(dirname "$0")/../backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="citadel_marketing_${TIMESTAMP}.sql.gz"

echo "Backing up database..."
docker compose -f docker/compose.yml exec -T postgres \
    pg_dump -U citadel citadel_marketing | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup saved: ${BACKUP_DIR}/${FILENAME}"

# Keep only last 30 backups
cd "$BACKUP_DIR"
ls -t *.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
echo "Old backups cleaned (keeping last 30)"
