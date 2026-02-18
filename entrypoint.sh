#!/bin/bash
set -e

# Берём порт из окружения Railway, если не задан — дефолт 8080
PORT=${PORT:-8080}

echo "Starting migrations..."
alembic upgrade head

echo "Starting Uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
chmod +x entrypoint.sh
