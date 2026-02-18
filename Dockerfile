# Social Wishlist API — production image
FROM python:3.12-slim

# Рабочая папка
WORKDIR /app

# Системные зависимости для asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python зависимости
COPY pyproject.toml ./ 
RUN pip install --no-cache-dir -e .

# Копируем Alembic и приложение
COPY alembic.ini ./ 
COPY alembic ./alembic
COPY app ./app

# Копируем entrypoint и делаем его исполняемым
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Экспонируем порт (не обязателен, но полезно для локального теста)
EXPOSE 8000

# ENTRYPOINT — гарантированно подставляет PORT
ENTRYPOINT ["./entrypoint.sh"]
