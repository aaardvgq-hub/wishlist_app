# Social Wishlist API

Production-ready FastAPI backend: async SQLAlchemy 2.0, PostgreSQL, Alembic, repository + service layer, UUID primary keys.

**Полное описание доработок, запуска и проверки — см. [DEMO.md](DEMO.md).**

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running and reachable)
- `.env` file (copy from `.env.example`)

## Setup

```bash
# Create virtualenv and install
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Copy env and set DATABASE_URL to your Postgres (async driver required)
copy .env.example .env
# Edit .env: DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

## Running migrations (Alembic)

Migrations are in `alembic/versions`. The DB URL is taken from your `.env` (via `app.core.config`).

**Apply all migrations (create/update schema):**

```bash
alembic upgrade head
```

**Create a new migration after changing models:**

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

**Roll back one revision:**

```bash
alembic downgrade -1
```

**Show current revision:**

```bash
alembic current
```

**Show migration history:**

```bash
alembic history
```

**Offline SQL (no DB connection):**

```bash
alembic upgrade head --sql
```

Ensure `DATABASE_URL` in `.env` uses the async driver: `postgresql+asyncpg://...`. The app and Alembic both use this URL.

## Run the app

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  
- Readiness (DB): http://localhost:8000/api/health/ready  

## Project layout

```
app/
  main.py              # FastAPI app, lifespan, routers
  core/                # config, database, security
  models/              # SQLAlchemy models (base + User)
  schemas/             # Pydantic v2 schemas
  repositories/        # persistence layer
  services/            # business logic
  api/routers/         # health, users (example)
  dependencies/        # get_db, get_user_service, etc.
  websocket/           # real-time (stub)
alembic/               # migrations
  env.py               # async env, uses app config
  versions/
```

## First-time DB setup

1. Create a PostgreSQL database (e.g. `wishlist`).
2. Set `DATABASE_URL` in `.env` to `postgresql+asyncpg://user:password@host:5432/wishlist`.
3. Run `alembic upgrade head` to create the `users` table (and any later migrations).

## Deployment (Docker)

- Build: `docker build -t wishlist-api .`
- Run: ensure `DATABASE_URL`, `SECRET_KEY`, and optionally `CORS_ORIGINS` and `REDIS_URL` are set (env or `.env`).
- **Migrations**: run before starting the app, e.g. `alembic upgrade head` in CI or an entrypoint script, or:  
  `docker run ... wishlist-api sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`
