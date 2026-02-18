#!/bin/sh
# entrypoint.sh — запускаем миграции и uvicorn

# Если PORT не задан, по умолчанию 8000
: "${PORT:=8000}"

echo "Starting migrations..."
alembic upgrade head

echo "Starting Uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
