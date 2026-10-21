#!/bin/bash
# Runs once, on first volume initialisation, as the Postgres superuser.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  -v hub_pw="$HUB_APP_PASSWORD" -v ro_pw="$CHATBOT_RO_PASSWORD" <<'SQL'
CREATE ROLE hub_app LOGIN PASSWORD :'hub_pw';
CREATE ROLE chatbot_ro LOGIN PASSWORD :'ro_pw';
CREATE DATABASE hub OWNER hub_app;
ALTER ROLE chatbot_ro SET default_transaction_read_only = on;
ALTER ROLE chatbot_ro SET statement_timeout = '5s';
ALTER ROLE chatbot_ro SET search_path = hub;
SQL
