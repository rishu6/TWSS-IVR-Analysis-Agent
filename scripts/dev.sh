#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  echo 'Install the Python and frontend dependencies first; see README.md.'
  exit 1
fi
export PYTHONPATH=backend
.venv/bin/alembic -c backend/alembic.ini upgrade head
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log &
callatlas_api_pid=$!
trap 'kill "$callatlas_api_pid" 2>/dev/null || true' EXIT INT TERM
npm --prefix frontend run dev -- --port 5173
