#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

"$DEPLOY_DIR/scripts/check.sh"

compose up --detach --build db web

echo "Esperando health check de Django..."
attempt=0
while [ "$attempt" -lt 30 ]; do
    status=$(compose ps --format json web 2>/dev/null || true)
    if printf '%s' "$status" | grep -q 'healthy'; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

[ "$attempt" -lt 30 ] || {
    compose logs --tail 100 web db
    die "Django no alcanzó estado saludable."
}

if ! compose exec -T web python manage.py shell -c \
    "from django.contrib.auth import get_user_model; raise SystemExit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)"; then
    echo "No existe un superusuario. Créalo ahora:"
    compose exec web python manage.py createsuperuser
fi

echo "Siptic Manager está activo detrás de 127.0.0.1:$(env_value APP_INTERNAL_PORT)."
echo "Siguiente paso: configurar Apache con deploy/apache/configure.sh --check."
