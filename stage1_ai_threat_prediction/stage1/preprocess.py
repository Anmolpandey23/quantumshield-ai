"""Preprocessing and feature scaling for LightGBM and TabDDPM."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    CLASS_NAMES,
    CLASS_TO_ID,
    LIGHTGBM_FEATURES,
    TABDDPM_FEATURES,
)


class Preprocessor:
    """Preprocess 52 network flow features and class labels."""

    def __init__(self, features: list[str] | None = None, classes: list[str] | None = None) -> None:
        self.features = features or list(LIGHTGBM_FEATURES)
        self.classes = classes or list(CLASS_NAMES)
        self.mean = np.zeros(len(self.features), dtype=np.float32)
        self.std = np.ones(len(self.features), dtype=np.float32)

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        sub = df.copy()
        for f in self.features:
            if f not in sub.columns:
                sub[f] = 0.0
        x = sub[self.features].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(np.float64)
        z = np.log1p(np.clip(x, 0.0, None))
        self.mean = z.mean(axis=0).astype(np.float32)
        self.std = np.maximum(z.std(axis=0), 1e-3).astype(np.float32)

        # Classes
        if "Label" in df.columns:
            unique_labs = df["Label"].dropna().unique().tolist()
            if any(c not in self.classes for c in unique_labs):
                # keep canonical order
                all_c = list(self.classes)
                for u in unique_labs:
                    if u not in all_c:
                        all_c.append(str(u))
                self.classes = all_c
        return self

    @staticmethod
    def _log(x: np.ndarray) -> np.ndarray:
        return np.log1p(np.clip(x, 0.0, None))

    def transform(self, df_or_array: pd.DataFrame | np.ndarray) -> np.ndarray:
        if isinstance(df_or_array, pd.DataFrame):
            df = df_or_array.copy()
            for f in self.features:
                if f not in df.columns:
                    df[f] = 0.0
            x = df[self.features].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(np.float64)
        else:
            arr = np.asarray(df_or_array, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.shape[1] != len(self.features):
                out = np.zeros((arr.shape[0], len(self.features)), dtype=np.float64)
                k = min(arr.shape[1], len(self.features))
                out[:, :k] = arr[:, :k]
                arr = out
            x = np.nan_to_num(arr, nan=0.0)

        scaled = (self._log(x) - self.mean) / self.std
        return np.clip(scaled, -10.0, 10.0).astype(np.float32)

    def encode(self, labels: pd.Series | list[str] | np.ndarray) -> np.ndarray:
        idx_map = {c: i for i, c in enumerate(self.classes)}
        return np.array([idx_map.get(str(l), 0) for l in labels], dtype=np.int64)

    def to_dict(self) -> dict:
        return {
            "mean": self.mean.tolist(),
            "std": self.std.tolist(),
            "classes": self.classes,
            "features": self.features,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Preprocessor":
        p = cls(features=d.get("features", list(LIGHTGBM_FEATURES)), classes=d.get("classes", list(CLASS_NAMES)))
        p.mean = np.asarray(d["mean"], dtype=np.float32)
        p.std = np.asarray(d["std"], dtype=np.float32)
        return p
