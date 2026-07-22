#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

[ $# -eq 1 ] || die "Uso: $0 archivo.dump"
require_env_file

BACKUP_FILE=$1
[ -f "$BACKUP_FILE" ] || die "No existe $BACKUP_FILE"

echo "Esta operación reemplazará la base actual."
printf 'Escribe RESTAURAR para continuar: '
read -r confirmation
[ "$confirmation" = "RESTAURAR" ] || die "Restauración cancelada."

database_name=$(env_value DB_NAME)
database_user=$(env_value DB_USER)

"$DEPLOY_DIR/scripts/backup.sh"
compose stop web
compose cp "$BACKUP_FILE" db:/tmp/siptic_restore.dump

if compose exec -T db sh -c \
    'PGPASSWORD="$DB_PASSWORD" pg_restore --username="$DB_USER" --dbname="$POSTGRES_DB" --clean --if-exists --no-owner /tmp/siptic_restore.dump'; then
    compose exec -T db rm -f /tmp/siptic_restore.dump
    compose up --detach web
    echo "Base $database_name restaurada como $database_user."
else
    compose up --detach web
    die "La restauración falló. Se conservó el respaldo previo."
fi
