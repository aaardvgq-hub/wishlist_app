#!/bin/bash
set -e

# Если PORT не задан — дефолт 8080
PORT=${PORT:-8080}

# Применяем миграции
alembic upgrade head

# Запускаем сервер на нужном порту
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
