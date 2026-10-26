#!/bin/sh
set -eu
# Free Render services do not support a separate pre-deploy command.
alembic -c backend/alembic.ini upgrade head
python backend/scripts/initialize_hosted_demo.py
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
