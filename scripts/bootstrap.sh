#!/usr/bin/env bash
# Run once after cloning:  bash scripts/bootstrap.sh
set -e
git config core.hooksPath scripts/hooks
chmod +x scripts/hooks/* 2>/dev/null || true
echo "Git hooks enabled (secret check before commit, no direct push to main)."
echo "Next: create a venv for YOUR stage and install its requirements (see README)."
