#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

require_env_file
compose ps
compose exec -T web python manage.py check
compose exec -T web python manage.py showmigrations --plan | tail -n 12
compose exec -T db pg_isready -U postgres -d "$(env_value DB_NAME)"

curl --fail --silent \
    --header 'X-Forwarded-Proto: https' \
    "http://127.0.0.1:$(env_value APP_INTERNAL_PORT)/health/"
echo
