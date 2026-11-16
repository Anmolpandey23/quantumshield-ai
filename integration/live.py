"""Build an Orchestrator wired to the REAL Stage 1 + Stage 3 (falls back gracefully if models are not trained)."""
from __future__ import annotations

import os
import warnings

from . import ROOT  # noqa: F401  (importing the package puts every stage folder on sys.path)
from .orchestrator import Orchestrator


def build_live(n_qubits: int = 1024, critical_nodes: set[str] | None = None):
    """Returns (orchestrator, predictor_or_None). predictor is None until `python -m stage1.train` has been run."""
    from stage3.node_agent import NodeFleet
    from stage3.policy import SelfHealingPolicy

    crit = critical_nodes if critical_nodes is not None else {c for c in os.getenv("QS_CRITICAL_NODES", "10.0.0.2,10.0.0.3").split(",") if c}
    policy = SelfHealingPolicy.load(critical_nodes=crit)
    orch = Orchestrator(policy=policy, n_qubits=n_qubits)
    orch.fleet = NodeFleet(orch.signer.public_key)
    predictor = None
    try:
        from stage1.predictor import ThreatPredictor
        predictor = ThreatPredictor.load()
    except Exception as exc:                                         # missing models or torch
        warnings.warn(f"Stage 1 models not loaded ({exc}). The backend will use the stub predictor until you train them.")
    return orch, predictor
