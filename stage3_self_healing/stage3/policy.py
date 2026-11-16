"""The live Stage 3 policy used by the orchestrator.

    policy = SelfHealingPolicy.load(critical_nodes={"10.0.0.2"})
    policy.observe(stage1_output)                     # called for EVERY node report (keeps its memory fresh)
    d = policy.decide(stage1_output, stage2_output)   # {"action", "requires_approval", "reason", "source"}
    policy.on_applied(node_id, action)                # called after the signed command was applied

If no trained weights exist it falls back to a transparent rule (and says so), so the pipeline never breaks.
"""
from __future__ import annotations

import pathlib
import warnings

import numpy as np
import torch

from . import baselines
from .guardrails import ACTIONS, ISOLATE, ISOLATED, MONITORED, ONLINE, Guardrails, action_mask
from .ppo import ActorCritic

DEFAULT_WEIGHTS = pathlib.Path(__file__).resolve().parent.parent / "artifacts" / "ppo_policy.pt"
_STATUS_ID = {ONLINE: 0, MONITORED: 1, "isolated": 2}


class SelfHealingPolicy:
    wants_status = True

    def __init__(self, net: ActorCritic | None = None, guardrails: Guardrails | None = None):
        self.net, self.guardrails = net, guardrails or Guardrails()
        self.status: dict[str, str] = {}
        self.ema: dict[str, float] = {}
        self.last: dict[str, dict] = {}
        self.iso_obs: dict[str, int] = {}

    # ------------------------------------------------------------------ construction
    @classmethod
    def load(cls, weights: str | pathlib.Path | None = None, **guardrail_kw) -> "SelfHealingPolicy":
        path = pathlib.Path(weights or DEFAULT_WEIGHTS)
        net = None
        if path.exists():
            ck = torch.load(path, map_location="cpu", weights_only=True)
            net = ActorCritic(**ck["cfg"]); net.load_state_dict(ck["state"]); net.eval()
        else:
            warnings.warn(f"No trained PPO weights at {path}. Using the rule-based fallback. Run: python -m stage3.train")
        return cls(net, Guardrails(**guardrail_kw))

    # ------------------------------------------------------------------ memory
    def observe(self, s1: dict) -> None:
        n = s1["node_id"]
        self.status.setdefault(n, ONLINE)
        self.ema[n] = s1["risk_score_node"] if n not in self.ema else 0.5 * self.ema[n] + 0.5 * s1["risk_score_node"]
        self.last[n] = s1
        if self.status[n] == ISOLATED:
            self.iso_obs[n] = self.iso_obs.get(n, 0) + 1

    def on_applied(self, node_id: str, action: str) -> None:
        if action == "isolate":
            self.status[node_id], self.iso_obs[node_id] = ISOLATED, 0
            self.guardrails.record_isolation()
        elif action == "reconnect":
            self.status[node_id], self.iso_obs[node_id] = ONLINE, 0
        elif action == "monitor" and self.status.get(node_id) != ISOLATED:
            self.status[node_id] = MONITORED

    # ------------------------------------------------------------------ observation vector (same layout as the simulator)
    def _obs_matrix(self) -> tuple[list[str], np.ndarray]:
        nodes = list(self.last)
        n_iso = sum(1 for v in self.status.values() if v == ISOLATED)
        iso_frac = n_iso / max(len(nodes), 1)
        mean_risk = float(np.mean([self.ema[n] for n in nodes])) if nodes else 0.0
        rows = []
        for n in nodes:
            s1, st = self.last[n], self.status.get(n, ONLINE)
            others = [self.ema[m] for m in nodes if m != n]
            rows.append([s1["risk_score_node"], s1["confidence"], s1["anomaly_score"],
                         st == ONLINE, st == MONITORED, st == ISOLATED, min(self.iso_obs.get(n, 0), 10) / 10,
                         float(np.mean(others)) if others else mean_risk, iso_frac, self.ema[n],
                         n in self.guardrails.critical_nodes])
        return nodes, np.array(rows, np.float32)

    # ------------------------------------------------------------------ decision
    def decide(self, s1: dict, s2: dict | None = None) -> dict:
        self.observe(s1) if s1["node_id"] not in self.last else None
        node = s1["node_id"]
        nodes, obs = self._obs_matrix()
        st = np.array([_STATUS_ID[self.status.get(n, ONLINE)] for n in nodes])
        mask = action_mask(st)
        i = nodes.index(node)
        if self.net is not None:
            proposed, source = ACTIONS[int(self.net.act_greedy(obs, mask)[i])], "ppo"
        else:
            proposed, source = ACTIONS[int(baselines.rule_policy(obs, mask)[i])], "rule_fallback"
        action, needs_human, reason = self.guardrails.check(proposed, s1, self.status)
        if action != proposed and not needs_human:
            source = "guardrail"
        return {"action": action, "requires_approval": needs_human, "reason": reason, "source": source,
                "proposed": proposed}

    def __call__(self, s1: dict, s2: dict) -> str:          # plain-callable compatibility with the Stage 3 stub
        self.observe(s1)
        d = self.decide(s1, s2)
        return "monitor" if d["requires_approval"] else d["action"]
