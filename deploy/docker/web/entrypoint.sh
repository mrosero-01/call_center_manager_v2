#!/bin/sh
set -eu

python - <<'PY'
import os
import time

import psycopg

deadline = time.monotonic() + 60

while True:
    try:
        with psycopg.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
        ):
            break
    except psycopg.OperationalError:
        if time.monotonic() >= deadline:
            raise
        time.sleep(2)
PY

python manage.py migrate --noinput
python manage.py grant_asterisk_access --role "${ASTERISK_DB_USER}"
python manage.py collectstatic --noinput

exec "$@"
