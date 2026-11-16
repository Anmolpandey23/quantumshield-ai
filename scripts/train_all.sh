#!/usr/bin/env bash
# Train Stage 1 and Stage 3.  Usage:  bash scripts/train_all.sh [synthetic | cicids <folder>]
set -e
SRC=${1:-synthetic}
(cd stage1_ai_threat_prediction && if [ "$SRC" = "cicids" ]; then python -m stage1.train --data cicids --data-dir "$2"; else python -m stage1.train --data synthetic; fi)
(cd stage3_self_healing && python -m stage3.train && python -m stage3.evaluate)
