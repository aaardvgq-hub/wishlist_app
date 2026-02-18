#!/usr/bin/env bash
set -e

alembic upgrade head
echo "Starting app (python -m app.main)..."
exec python -m app.main
