"""ThreatPredictor: the object the rest of the project uses.

    pred = ThreatPredictor.load()               # reads artifacts/ written by `python -m stage1.train`
    pred.ingest(flows_df)                       # keep a rolling window of recent flows
    out = pred.predict("192.168.1.14")          # -> dict that satisfies contracts/stage1_output.schema.json
"""
from __future__ import annotations

import json
import pathlib
from typing import Iterable

import numpy as np
import pandas as pd
import torch

from .classifier import FlowClassifier
from .config import ARTIFACTS_DIR, BENIGN, FEATURES
from .cpc import CPCTransformer
from .dygnn import DyGNN, build_snapshots, node_risk
from .explain import top_reasons
from .preprocess import Preprocessor

CONTRACT_VERSION = "1.0"


class ThreatPredictor:
    def __init__(self, prep: Preprocessor, clf: FlowClassifier, cpc: CPCTransformer, gnn: DyGNN, cfg: dict,
                 device: str = "cpu"):
        self.prep, self.clf, self.cpc, self.gnn, self.cfg, self.device = prep, clf, cpc, gnn, cfg, device
        self.seq_len = cpc.seq_len
        self.w = cfg.get("fusion", {"gnn": 0.45, "classifier": 0.35, "cpc": 0.20})
        self.buffer = pd.DataFrame()
        self._cache: dict | None = None

    # ------------------------------------------------------------------ io
    @classmethod
    def load(cls, path: str | pathlib.Path | None = None, device: str = "cpu") -> "ThreatPredictor":
        p = pathlib.Path(path or ARTIFACTS_DIR)
        if not (p / "config.json").exists():
            raise FileNotFoundError(f"No trained Stage 1 models in '{p}'. Run: python -m stage1.train --data synthetic")
        cfg = json.loads((p / "config.json").read_text())
        prep = Preprocessor.from_dict(json.loads((p / "preprocessor.json").read_text()))
        clf = FlowClassifier(**torch.load(p / "classifier.pt", map_location=device, weights_only=True)["cfg"]).to(device)
        clf.load_state_dict(torch.load(p / "classifier.pt", map_location=device, weights_only=True)["state"])
        ck = torch.load(p / "cpc.pt", map_location=device, weights_only=True)
        cpc = CPCTransformer(**ck["cfg"]).to(device); cpc.load_state_dict(ck["state"]); cpc.calib = ck["calib"]
        ck = torch.load(p / "dygnn.pt", map_location=device, weights_only=True)
        gnn = DyGNN(**ck["cfg"]).to(device); gnn.load_state_dict(ck["state"])
        return cls(prep, clf, cpc, gnn, cfg, device)

    # ------------------------------------------------------------------ streaming window
    def ingest(self, flows: pd.DataFrame) -> None:
        """Add new flows (columns: FEATURES + Source IP, Destination IP, Timestamp). Old flows fall out."""
        flows = flows.copy()
        flows["Timestamp"] = pd.to_datetime(flows["Timestamp"])
        self.buffer = pd.concat([self.buffer, flows], ignore_index=True) if len(self.buffer) else flows
        horizon = pd.Timedelta(minutes=self.cfg.get("buffer_minutes", 15))
        self.buffer = self.buffer[self.buffer["Timestamp"] >= self.buffer["Timestamp"].max() - horizon].reset_index(drop=True)
        self._cache = None

    def _graph_risk(self) -> dict[str, float]:
        if self._cache is not None:
            return self._cache
        if self.buffer.empty:
            self._cache = {}
            return self._cache
        df = self.buffer
        idx = {ip: i for i, ip in enumerate(pd.concat([df["Source IP"], df["Destination IP"]]).unique())}
        snaps = build_snapshots(df, self.prep.transform(df), idx, self.cfg.get("snapshot_seconds", 60), with_labels=False)
        risk = node_risk(self.gnn, snaps[-self.cfg.get("gnn_context_snapshots", 6):], len(idx))
        inv = {i: ip for ip, i in idx.items()}
        self._cache = {inv[g]: r for g, r in risk.items()}
        return self._cache

    # ------------------------------------------------------------------ prediction
    def predict(self, node_id: str) -> dict:
        rows = self.buffer[self.buffer["Source IP"] == node_id] if len(self.buffer) else self.buffer
        if rows.empty:
            return self._out(node_id, BENIGN, 0.5, 0.0, 0.0, ["no recent traffic from this node"])
        recent = rows.tail(max(self.seq_len, 40))
        x = self.prep.transform(recent)
        classes = self.prep.classes

        proba = self.clf.predict_proba(x).mean(0)
        k = int(proba.argmax()); label, conf = classes[k], float(proba[k])
        p_attack = float(1 - proba[classes.index(BENIGN)])

        seq = x[-self.seq_len:]
        if len(seq) < self.seq_len:                          # too few flows yet: pad by repeating the first
            seq = np.concatenate([np.repeat(seq[:1], self.seq_len - len(seq), 0), seq])
        anomaly = float(self.cpc.score(seq[None])[0])
        gnn = float(self._graph_risk().get(node_id, 0.0))

        w = self.w
        risk = float(np.clip(w["gnn"] * gnn + w["classifier"] * p_attack + w["cpc"] * anomaly, 0, 1))
        reasons: list[str] = []
        unknown = False
        if label == BENIGN and anomaly >= 0.9 and risk >= 0.6:       # looks normal to the classifier, but is badly predicted
            label, conf, unknown = "ANOMALY_UNKNOWN", anomaly, True
            reasons.append("behaviour deviates strongly from this host's learned normal pattern")
        if label != BENIGN:
            target = int(np.argsort(-proba)[1]) if unknown else k
            reasons += top_reasons(self.clf.attribution(x, target), x.mean(0))
            if gnn >= 0.7:
                reasons.append("communicates with other risky hosts (graph model)")
            if anomaly >= 0.7 and not unknown:
                reasons.append("traffic pattern is not what the sequence model expected")
        return self._out(node_id, label, conf, anomaly, risk, reasons)

    def predict_all(self, nodes: Iterable[str] | None = None) -> list[dict]:
        nodes = list(nodes) if nodes is not None else (list(self.buffer["Source IP"].unique()) if len(self.buffer) else [])
        return [self.predict(n) for n in nodes]

    @staticmethod
    def _out(node_id: str, label: str, conf: float, anomaly: float, risk: float, reasons: list[str]) -> dict:
        r = lambda v: round(float(np.clip(v, 0.0, 1.0)), 4)
        return {"contract_version": CONTRACT_VERSION, "node_id": node_id, "threat_label": label,
                "confidence": r(conf), "anomaly_score": r(anomaly), "risk_score_node": r(risk),
                "explanation": reasons[:4]}
