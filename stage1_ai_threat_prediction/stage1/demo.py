"""See Stage 1 work:  python -m stage1.demo   (needs `python -m stage1.train` first)"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from .config import BENIGN
from .data import make_synthetic
from .predictor import ThreatPredictor


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", default=None)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    pred = ThreatPredictor.load(a.artifacts)
    df = make_synthetic(seed=a.seed, n_minutes=60, n_episodes=6)        # a network the models have never seen
    att = df[df["Label"] != BENIGN]
    t = att["Timestamp"].iloc[len(att) // 3] + pd.Timedelta(minutes=3)  # a moment while an attack is running
    pred.ingest(df[df["Timestamp"] <= t])
    outs = sorted(pred.predict_all(), key=lambda o: -o["risk_score_node"])
    truth = df[df["Timestamp"] <= t].groupby("Source IP")["Label"].agg(lambda s: s.iloc[-1])
    print(f"Network state at {t}. Top 5 riskiest hosts:\n")
    for o in outs[:5]:
        print(json.dumps(o))
        print(f"   ground truth: {truth[o['node_id']]}")


if __name__ == "__main__":
    main()
