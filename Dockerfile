# Social Wishlist API — production image
# Run migrations before start: alembic upgrade head (or use entrypoint script).
FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg (optional, slim has minimal libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from pyproject.toml (no dev deps in image)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Default: run app. For migrations-on-startup, use:
# CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
# force rebuild
CMD ["bash", "-lc", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080"]


