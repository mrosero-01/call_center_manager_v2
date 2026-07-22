#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../scripts/common.sh"

MODE=${1:---check}
case "$MODE" in
    --check|--dry-run|--apply) ;;
    *) die "Uso: $0 --check|--dry-run|--apply" ;;
esac

require_env_file
require_command apache2ctl

domain=$(env_value DJANGO_ALLOWED_HOSTS | cut -d, -f1)
port=$(env_value APP_EXTERNAL_PORT)
internal_port=$(env_value APP_INTERNAL_PORT)
certificate=$(env_value APACHE_CERTIFICATE_FILE)
certificate_key=$(env_value APACHE_CERTIFICATE_KEY_FILE)

[ -f "$certificate" ] || die "No existe el certificado $certificate"
[ -f "$certificate_key" ] || die "No existe la llave $certificate_key"

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"; then
    if ! grep -RqsE "<VirtualHost[[:space:]]+\*:$port>" \
        /etc/apache2/sites-enabled/siptic-manager.conf 2>/dev/null; then
        die "El puerto $port ya está ocupado por otro servicio o VirtualHost."
    fi
fi

rendered=$(mktemp)
trap 'rm -f "$rendered"' EXIT

sed \
    -e "s@__DOMAIN__@$domain@g" \
    -e "s@__PORT__@$port@g" \
    -e "s@__INTERNAL_PORT__@$internal_port@g" \
    -e "s@__CERTIFICATE_FILE__@$certificate@g" \
    -e "s@__CERTIFICATE_KEY_FILE__@$certificate_key@g" \
    "$SCRIPT_DIR/siptic-manager.conf.example" > "$rendered"

if grep -RqsE "^[[:space:]]*Listen[[:space:]]+$port([[:space:]]|$)" \
    /etc/apache2/ports.conf /etc/apache2/sites-enabled /etc/apache2/conf-enabled; then
    sed -i "/^Listen $port$/d" "$rendered"
fi

if [ "$MODE" = "--dry-run" ]; then
    cat "$rendered"
    exit 0
fi

for module in ssl proxy proxy_http headers; do
    apache2ctl -M 2>/dev/null | grep -q "${module}_module" || {
        [ "$MODE" = "--apply" ] || die "Falta el módulo Apache $module."
    }
done

if [ "$MODE" = "--check" ]; then
    echo "Certificado, dominio y plantilla Apache válidos."
    echo "Ejecuta $0 --dry-run para revisar el VirtualHost."
    exit 0
fi

[ "$(id -u)" -eq 0 ] || die "--apply requiere root."

target=/etc/apache2/sites-available/siptic-manager.conf
backup_dir=/var/backups/siptic-manager/apache/$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$backup_dir"
[ ! -e "$target" ] || cp -a "$target" "$backup_dir/"

for module in ssl proxy proxy_http headers; do
    a2enmod "$module" >/dev/null
done
install -m 0644 "$rendered" "$target"
a2ensite siptic-manager >/dev/null

if ! apache2ctl configtest; then
    a2dissite siptic-manager >/dev/null || true
    die "Apache rechazó la configuración. Revisa $backup_dir."
fi

systemctl reload apache2
echo "Apache publica Siptic Manager en https://$domain:$port"
