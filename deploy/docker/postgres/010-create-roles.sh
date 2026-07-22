#!/bin/sh
set -eu

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=database_name="$POSTGRES_DB" \
  --set=app_password="$DB_PASSWORD" \
  --set=asterisk_password="$ASTERISK_DB_PASSWORD" <<'SQL'
CREATE ROLE callcenter_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE ROLE asterisk_schedule_reader LOGIN PASSWORD :'asterisk_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT CONNECT ON DATABASE :"database_name" TO callcenter_app, asterisk_schedule_reader;
GRANT USAGE, CREATE ON SCHEMA public TO callcenter_app;
GRANT USAGE ON SCHEMA public TO asterisk_schedule_reader;
SQL
