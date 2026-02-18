#!/bin/bash
set -e

# Применяем миграции
alembic upgrade head

# Запускаем uvicorn на фиксированном порту 8080
uvicorn app.main:app --host 0.0.0.0 --port 8080
