"""Traffic generators so the dashboard has something to show before you have real traffic.

StubSimulator   : needs nothing but this repo. Fakes Stage 1 outputs for a small network.
ReplaySimulator : replays a synthetic network through the REAL Stage 1 models (needs trained models).
"""
from __future__ import annotations

import random

from .config import SIM_NODES

ATTACKS = {
    "DDoS": ["unusual packet rate", "spike in SYN flag ratio"],
    "PortScan": ["many connection resets (RST)", "tiny outgoing data volume"],
    "BruteForce": ["spike in PSH flag count", "many reply packets"],
    "DoS": ["unusually long connections", "long gaps between packets"],
    "Bot": ["robot-like regular packet timing", "long active periods"],
    "WebAttack": ["large outgoing data volume", "unusually large biggest packet"],
}


def fake_stage1(node_id: str, attack: str | None, rng: random.Random) -> dict:
    if attack:
        conf, anom = rng.uniform(0.82, 0.99), rng.uniform(0.6, 0.97)
        return {"contract_version": "1.0", "node_id": node_id, "threat_label": attack, "confidence": round(conf, 3),
                "anomaly_score": round(anom, 3), "risk_score_node": round(min(0.99, 0.55 * conf + 0.45 * anom + 0.05), 3),
                "explanation": ATTACKS[attack][: rng.randint(1, 2)]}
    return {"contract_version": "1.0", "node_id": node_id, "threat_label": "BENIGN", "confidence": round(rng.uniform(0.9, 0.995), 3),
            "anomaly_score": round(rng.uniform(0.01, 0.15), 3), "risk_score_node": round(rng.uniform(0.01, 0.12), 3), "explanation": []}


class StubSimulator:
    name = "stub"

    def __init__(self, n_nodes: int = SIM_NODES, seed: int | None = None):
        self.rng = random.Random(seed)
        self.nodes = [f"10.0.0.{i + 2}" for i in range(n_nodes)]
        self.infected: dict[str, tuple[str, int]] = {}          # node -> (attack type, ticks left once quarantined)

    def tick(self, status: dict[str, str]) -> list[tuple[dict, float]]:
        """Return [(stage1_output, eve_fraction)] for this tick. `status` is the orchestrator's node status."""
        out = []
        for n in self.nodes:
            if n in self.infected:
                atk, left = self.infected[n]
                if status.get(n) == "isolated":                  # remediation happens in quarantine
                    left -= 1
                    if left <= 0:
                        del self.infected[n]
                    else:
                        self.infected[n] = (atk, left)
            elif len(self.infected) < 3 and status.get(n) != "isolated" and self.rng.random() < 0.07:
                self.infected[n] = (self.rng.choice(list(ATTACKS)), self.rng.randint(2, 4))
            s1 = fake_stage1(n, self.infected[n][0] if n in self.infected else None, self.rng)
            eve = 1.0 if n in self.infected and self.rng.random() < 0.15 else 0.0     # sometimes someone is listening
            out.append((s1, eve))
        return out


class ReplaySimulator:
    """Feeds one minute of a synthetic network per tick into the real predictor."""
    name = "replay"

    def __init__(self, predictor, seed: int | None = None):
        from stage1.data import make_synthetic
        self.pred = predictor
        self.df = make_synthetic(seed=seed or random.randint(1, 10_000), n_minutes=90, n_hosts=SIM_NODES, n_episodes=8)
        self.t0, self.minute = self.df["Timestamp"].min(), 0
        self.n_minutes = 90

    def tick(self, status: dict[str, str]) -> list[tuple[dict, float]]:
        import pandas as pd
        lo = self.t0 + pd.Timedelta(minutes=self.minute)
        chunk = self.df[(self.df["Timestamp"] >= lo) & (self.df["Timestamp"] < lo + pd.Timedelta(minutes=1))]
        self.minute = (self.minute + 1) % self.n_minutes
        if chunk.empty:
            return []
        self.pred.ingest(chunk)
        return [(self.pred.predict(n), 0.0) for n in chunk["Source IP"].unique()]
