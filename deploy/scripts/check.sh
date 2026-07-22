#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

require_command docker
require_command curl
require_env_file
docker compose version >/dev/null

for placeholder in replace-with your-long-random example.com; do
    if grep -q "$placeholder" "$ENV_FILE"; then
        die "Quedó un valor de ejemplo en $ENV_FILE: $placeholder"
    fi
done

compose config --quiet

[ "$(env_value DB_USER)" = "callcenter_app" ] || die "DB_USER debe ser callcenter_app."
[ "$(env_value ASTERISK_DB_USER)" = "asterisk_schedule_reader" ] || \
    die "ASTERISK_DB_USER debe ser asterisk_schedule_reader."

internal_port=$(env_value APP_INTERNAL_PORT)
database_port=$(env_value ASTERISK_DB_PORT)

for port in "$internal_port" "$database_port"; do
    if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"; then
        if ! compose ps --services --filter status=running 2>/dev/null | grep -q .; then
            die "El puerto local $port ya está ocupado."
        fi
    fi
done

echo "Configuración Docker válida."
echo "Django interno: 127.0.0.1:$internal_port"
echo "PostgreSQL para Asterisk: 127.0.0.1:$database_port"
