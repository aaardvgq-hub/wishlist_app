#!/usr/bin/env bash
set -e

# Alembic миграции
alembic upgrade head

# Подставляем PORT по умолчанию (для локала)
PORT=${PORT:-8000}

# Запуск приложения
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
