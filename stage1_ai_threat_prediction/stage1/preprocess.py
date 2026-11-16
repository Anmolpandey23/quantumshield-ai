"""log1p + standardisation. Fitted on the TRAIN split only, then saved next to the models."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BENIGN, FEATURES


class Preprocessor:
    def __init__(self) -> None:
        self.mean = np.zeros(len(FEATURES), np.float32)
        self.std = np.ones(len(FEATURES), np.float32)
        self.classes: list[str] = []

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        z = self._log(df[FEATURES].to_numpy(np.float64))
        self.mean = z.mean(0).astype(np.float32)
        self.std = np.maximum(z.std(0), 1e-3).astype(np.float32)
        labs = sorted(df["Label"].unique(), key=lambda c: (c != BENIGN, c))   # BENIGN is always index 0
        self.classes = list(labs)
        return self

    @staticmethod
    def _log(x: np.ndarray) -> np.ndarray:
        return np.log1p(np.clip(x, 0, None))

    def transform(self, df_or_array) -> np.ndarray:
        x = df_or_array[FEATURES].to_numpy(np.float64) if isinstance(df_or_array, pd.DataFrame) else np.asarray(df_or_array, np.float64)
        return np.clip((self._log(x) - self.mean) / self.std, -10, 10).astype(np.float32)

    def encode(self, labels) -> np.ndarray:
        idx = {c: i for i, c in enumerate(self.classes)}
        return np.array([idx.get(l, -1) for l in labels], dtype=np.int64)

    def to_dict(self) -> dict:
        return {"mean": self.mean.tolist(), "std": self.std.tolist(), "classes": self.classes, "features": FEATURES}

    @classmethod
    def from_dict(cls, d: dict) -> "Preprocessor":
        if d["features"] != FEATURES:
            raise ValueError("Feature list changed since training: retrain Stage 1.")
        p = cls()
        p.mean, p.std, p.classes = np.array(d["mean"], np.float32), np.array(d["std"], np.float32), list(d["classes"])
        return p
