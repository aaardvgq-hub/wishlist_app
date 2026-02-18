#!/bin/sh
# entrypoint.sh — запускает миграции и uvicorn

# Подставляем порт из ENV, по умолчанию 8000
PORT=${PORT:-8000}

echo "Starting migrations..."
alembic upgrade head
echo "Migrations finished."

# Запускаем uvicorn на нужном порту
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
