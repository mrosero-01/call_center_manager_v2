#!/bin/sh
set -eu

DEPLOY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGET=$DEPLOY_DIR/.env.production

[ $# -ge 1 ] || {
    echo "Uso: $0 dominio [puerto_externo]" >&2
    exit 1
}

DOMAIN=$1
PORT=${2:-4000}

printf '%s' "$DOMAIN" | grep -Eq '^[A-Za-z0-9.-]+$' || {
    echo "Dominio inválido." >&2
    exit 1
}
printf '%s' "$PORT" | grep -Eq '^[0-9]+$' || {
    echo "Puerto inválido." >&2
    exit 1
}
[ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ] || {
    echo "Puerto fuera de rango." >&2
    exit 1
}
[ ! -e "$TARGET" ] || {
    echo "$TARGET ya existe; no se sobrescribió." >&2
    exit 1
}

python3 - "$DEPLOY_DIR/.env.production.example" "$TARGET" "$DOMAIN" "$PORT" <<'PY'
import secrets
import sys
from pathlib import Path

source, target, domain, port = sys.argv[1:]
text = Path(source).read_text()
text = text.replace("empresa.com", domain)
text = text.replace("APP_EXTERNAL_PORT=4000", f"APP_EXTERNAL_PORT={port}")
text = text.replace(":4000", f":{port}")
replacements = {
    "replace-with-at-least-64-random-characters": secrets.token_urlsafe(64),
    "replace-with-a-long-random-app-password": secrets.token_urlsafe(36),
    "replace-with-a-different-postgres-admin-password": secrets.token_urlsafe(36),
    "replace-with-a-long-random-readonly-password": secrets.token_urlsafe(36),
}
for old, new in replacements.items():
    text = text.replace(old, new)
Path(target).write_text(text)
PY

chmod 600 "$TARGET"
echo "Configuración creada en $TARGET"
