#!/bin/sh
set -eu

DEPLOY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$DEPLOY_DIR/.." && pwd)
ENV_FILE=${SIPTIC_ENV_FILE:-$DEPLOY_DIR/.env.production}
COMPOSE_FILE=$DEPLOY_DIR/compose.yaml

die() {
    echo "ERROR: $*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Falta el comando: $1"
}

require_env_file() {
    [ -f "$ENV_FILE" ] || die "Falta $ENV_FILE. Ejecuta deploy/scripts/init-env.sh."
    [ "$(stat -c %a "$ENV_FILE")" = "600" ] || die "$ENV_FILE debe tener permisos 600."
}

compose() {
    docker compose \
        --env-file "$ENV_FILE" \
        --file "$COMPOSE_FILE" \
        "$@"
}

env_value() {
    key=$1
    value=$(sed -n "s/^${key}=//p" "$ENV_FILE" | tail -n 1)
    [ -n "$value" ] || die "Falta ${key} en $ENV_FILE"
    printf '%s' "$value"
}
