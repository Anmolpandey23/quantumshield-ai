#!/usr/bin/env bash
# One command: install, test, demo, experiments.   Usage: bash scripts/run_everything.sh
set -e
python3 -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements.txt
python -m pytest -q
python -m stage2.demo
python -m experiments.run_all
echo "All done. Open results/RESULTS.md"
