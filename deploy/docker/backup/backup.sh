#!/bin/sh
set -eu

backup_dir=/backups
retention_days="${BACKUP_RETENTION_DAYS:-14}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$backup_dir/callcenter_manager_$timestamp.dump"

mkdir -p "$backup_dir"

PGPASSWORD="$DB_PASSWORD" pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --format=custom \
  --no-owner \
  --file="$target"

find "$backup_dir" -type f -name 'callcenter_manager_*.dump' \
  -mtime "+$retention_days" -delete

echo "Respaldo creado: $target"
