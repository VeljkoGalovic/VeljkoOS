#!/bin/sh
# Bring the schema up to date, then serve. Compose gates this container behind a
# Postgres healthcheck, so the database is already accepting connections by the
# time migrations run.
set -e

echo "[entrypoint] applying migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
