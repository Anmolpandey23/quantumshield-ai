"""Stand-ins for Stage 1 and Stage 3 so the pipeline runs end to end TODAY.

Stage 1 owner: replace `stage1_stub` with your real predictor (same output shape).
Stage 3 owner: replace `stage3_policy_stub` with your trained RL agent (same inputs/outputs).
"""
from __future__ import annotations


def stage1_stub(node_id: str, attack: bool = True) -> dict:
    if attack:
        return {"contract_version": "1.0", "node_id": node_id, "threat_label": "DDoS", "confidence": 0.94,
                "anomaly_score": 0.87, "risk_score_node": 0.91,
                "explanation": ["unusual packet rate", "spike in SYN flag ratio"]}
    return {"contract_version": "1.0", "node_id": node_id, "threat_label": "BENIGN", "confidence": 0.98,
            "anomaly_score": 0.04, "risk_score_node": 0.05, "explanation": []}


def stage3_policy_stub(stage1: dict, stage2: dict) -> str:
    """Return 'isolate', 'monitor' or 'reconnect'. Simple rule, NOT the RL agent."""
    if stage1["threat_label"] != "BENIGN" and stage1["risk_score_node"] >= 0.8 and stage1["confidence"] >= 0.8:
        return "isolate"
    return "monitor"
