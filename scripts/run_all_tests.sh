#!/usr/bin/env bash
# Runs every stage's tests. From the repo root:  bash scripts/run_all_tests.sh
set -e
echo "== integration";   python -m pytest -q
for d in stage1_ai_threat_prediction stage2_quantum_cryptography stage3_self_healing backend_dashboard; do
  echo "== $d"; (cd "$d" && python -m pytest -q)
done
if [ -d frontend/node_modules ]; then echo "== frontend"; (cd frontend && npm test --silent); else echo "== frontend skipped (run: cd frontend && npm install)"; fi
echo "ALL GREEN"
