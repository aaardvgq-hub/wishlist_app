FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./ 
RUN pip install --no-cache-dir -e .

COPY alembic.ini ./ 
COPY alembic ./alembic
COPY app ./app

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

ENV PYTHONUNBUFFERED=1
# PORT задаётся платформой (Railway и т.д.) или по умолчанию 8000 в app
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
