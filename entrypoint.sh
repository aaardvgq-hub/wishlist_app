#!/bin/sh
set -e

echo "Starting migrations..."
alembic upgrade head

echo "Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
