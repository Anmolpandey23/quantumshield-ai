"""Stage 1: AI threat prediction (TabDDPM Anomaly Detection + LightGBM Attack Classification + SHAP)."""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

__version__ = "1.0.0"

from .classifier import FlowClassifier
from .predictor import ThreatPredictor
from .tabddpm import TabDDPM, TabDDPMPreprocessor

__all__ = ["ThreatPredictor", "FlowClassifier", "TabDDPM", "TabDDPMPreprocessor"]
