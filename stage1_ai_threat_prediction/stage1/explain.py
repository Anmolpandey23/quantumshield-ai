"""Explainable AI: turn model attributions into short human reasons ('unusual packet rate')."""
from __future__ import annotations

import numpy as np

from .config import FEATURES, PHRASES


def top_reasons(attribution: np.ndarray, x_scaled_mean: np.ndarray, k: int = 3, min_abs_z: float = 1.0) -> list[str]:
    """Pick the k most influential features whose value is really unusual (|z| >= min_abs_z).

    attribution : |gradient x input| per feature (importance for the predicted class)
    x_scaled_mean : the node's average scaled flow; because scaling uses benign statistics, it IS the z-score.
    """
    reasons: list[str] = []
    for i in np.argsort(-attribution):
        z = float(x_scaled_mean[i])
        if abs(z) < min_abs_z:
            continue
        high, low = PHRASES[FEATURES[i]]
        phrase = high if z > 0 else low
        if phrase not in reasons:
            reasons.append(phrase)
        if len(reasons) == k:
            break
    return reasons
