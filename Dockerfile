# Social Wishlist API — production image
FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY alembic.ini ./ 
COPY alembic ./alembic
COPY app ./app

# Копируем entrypoint
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Жёсткий ENTRYPOINT — гарантированно подставляет PORT
ENTRYPOINT ["./entrypoint.sh"]
