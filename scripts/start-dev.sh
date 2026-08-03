#!/usr/bin/env bash
# scripts/start-dev.sh
# Start the full development stack without Docker.
# Usage: bash scripts/start-dev.sh

set -euo pipefail

echo "Starting MicroFlow development environment..."

# Backend
(
  cd backend
  if [ ! -d ".venv" ]; then
    python -m venv .venv
  fi
  source .venv/bin/activate
  pip install -r requirements.txt --quiet
  cp -n .env.example .env 2>/dev/null || true
  uvicorn app.main:app --reload --port 8000 &
  echo "Backend started on http://localhost:8000"
)

# Frontend
(
  cd frontend
  npm install --silent
  cp -n .env.example .env 2>/dev/null || true
  npm run dev &
  echo "Frontend started on http://localhost:5173"
)

wait
