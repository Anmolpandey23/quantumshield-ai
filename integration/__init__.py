"""Glue between the four stages.

Each stage folder is added to sys.path so stages can import each other
(`from stage2.pipeline import secure_channel`, `from stage1.predictor import ThreatPredictor`, ...).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGE_DIRS = ["stage2_quantum_cryptography", "stage1_ai_threat_prediction", "stage3_self_healing", "backend_dashboard"]
for _d in STAGE_DIRS:
    _p = str(ROOT / _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
