#!/usr/bin/env bash
# Starts the backend (port 8000) and the React dashboard together.  From the repo root:  bash scripts/dev_all.sh
# Needs: Python env with requirements-integration.txt installed, and Node 20+ (or Bun).  Ctrl+C stops both.
set -e
[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
( cd backend_dashboard && python -m uvicorn app.main:app --port 8000 ) &
BACK=$!
trap 'kill $BACK 2>/dev/null' EXIT
cd frontend
[ -d node_modules ] || { command -v bun >/dev/null && bun install || npm install; }
echo "Dashboard live mode needs VITE_USE_MOCK_DATA=false in frontend/.env"
command -v bun >/dev/null && bun run dev || npm run dev
