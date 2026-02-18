# Social Wishlist API — production image
FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Системные зависимости для asyncpg и PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Копируем проект
COPY alembic.ini ./ 
COPY alembic ./alembic
COPY app ./app

# Копируем entrypoint
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Настройки окружения
ENV PYTHONUNBUFFERED=1

# Экспонируем порт 8000 (по умолчанию, локально)
EXPOSE 8000

# ENTRYPOINT — запускаем entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
