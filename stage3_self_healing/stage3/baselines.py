"""Simple policies to compare the PPO agent against (and to use as the fallback if no model is trained)."""
from __future__ import annotations

import numpy as np

from .guardrails import ISOLATE, MONITOR, RECONNECT

# obs columns: 0 risk, 1 conf, 2 anomaly, 3 online, 4 monitored, 5 isolated, 6 iso_time/10, 7 nbr risk, 8 iso frac, 9 ema, 10 critical


def never_act(obs: np.ndarray, mask: np.ndarray, rng=None) -> np.ndarray:
    return np.full(obs.shape[:-1], MONITOR)


def random_policy(obs: np.ndarray, mask: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    p = mask / mask.sum(-1, keepdims=True)
    u = rng.random(obs.shape[:-1])[..., None]
    return (u > np.cumsum(p, -1)).sum(-1).clip(0, 2)


def rule_policy(obs: np.ndarray, mask: np.ndarray, rng=None, isolate_at: float = 0.6, reconnect_below: float = 0.3,
                min_iso_steps: int = 3) -> np.ndarray:
    """Hand-written rule: isolate when the smoothed risk is high, reconnect when it is low for a while."""
    ema, iso, iso_t = obs[..., 9], obs[..., 5] > 0.5, obs[..., 6] * 10
    act = np.full(ema.shape, MONITOR)
    act[(~iso) & (ema >= isolate_at)] = ISOLATE
    act[iso & (ema <= reconnect_below) & (iso_t >= min_iso_steps)] = RECONNECT
    return act
