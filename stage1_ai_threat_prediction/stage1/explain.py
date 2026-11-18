"""Explainable AI (XAI) for Stage 1: SHAP TreeExplainer feature contributions and human reasons."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from .config import LIGHTGBM_FEATURES, PHRASES


def format_explanation_phrases(top_contributing_features: list[dict[str, Any]], max_reasons: int = 4) -> list[str]:
    """Convert top SHAP contributing features into concise human dashboard phrases."""
    reasons: list[str] = []
    for item in top_contributing_features:
        phrase = item.get("phrase")
        if not phrase:
            feat = item.get("feature", "")
            impact = item.get("impact", "positive")
            pair = PHRASES.get(feat, ("unusual traffic metric", "unusual traffic metric"))
            phrase = pair[0] if impact == "positive" else pair[1]
        if phrase and phrase not in reasons:
            reasons.append(phrase)
        if len(reasons) >= max_reasons:
            break
    return reasons


def top_reasons(
    attribution: np.ndarray,
    x_scaled_mean: np.ndarray,
    k: int = 3,
    min_abs_z: float = 1.0,
    features: list[str] | None = None,
) -> list[str]:
    """Pick top influential features with notable deviations (legacy + general attribution support)."""
    feat_list = features or LIGHTGBM_FEATURES
    reasons: list[str] = []
    if len(attribution) == 0:
        return reasons

    for i in np.argsort(-np.abs(attribution)):
        if i >= len(feat_list) or i >= len(x_scaled_mean):
            continue
        z = float(x_scaled_mean[i])
        if abs(z) < min_abs_z:
            continue
        feat = feat_list[i]
        pair = PHRASES.get(feat, ("unusual value", "unusual value"))
        phrase = pair[0] if z > 0 else pair[1]
        if phrase not in reasons:
            reasons.append(phrase)
        if len(reasons) == k:
            break
    return reasons
