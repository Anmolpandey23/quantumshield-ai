"""Guardrails: hard limits the learned agent can never cross, plus the human-approval rule.

The RL agent only PROPOSES an action. These rules decide whether it may run.
  1. Allowlist      : only isolate / monitor / reconnect exist (nothing else can be expressed).
  2. Evidence       : isolate needs a real threat label and enough confidence.
  3. Blast radius   : never quarantine more than `max_isolated_fraction` of the network at once.
  4. Critical nodes : isolating a gateway/server needs a human to approve.
  5. Rate limit     : more than `max_isolations_per_minute` isolations needs a human to approve.
  6. Kill switch    : `enabled=False` turns the agent off (everything becomes 'monitor').
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

ACTIONS = ("monitor", "isolate", "reconnect")          # index 0, 1, 2 (same order everywhere)
MONITOR, ISOLATE, RECONNECT = 0, 1, 2
ONLINE, MONITORED, ISOLATED = "online", "monitored", "isolated"


def action_mask(status: np.ndarray) -> np.ndarray:
    """status: int array (0 online, 1 monitored, 2 isolated) -> bool mask (..., 3) of legal actions."""
    mask = np.ones(status.shape + (3,), dtype=bool)
    iso = status == 2
    mask[..., ISOLATE] = ~iso            # cannot isolate what is already isolated
    mask[..., RECONNECT] = iso           # can only reconnect what is isolated
    return mask


def enforce_isolation_cap(actions: np.ndarray, risk: np.ndarray, status: np.ndarray, max_fraction: float) -> np.ndarray:
    """Cancel the lowest-risk isolate actions until the isolated share of the network is <= max_fraction.

    actions/risk/status: shape (N,) for one network. Returns a new actions array (cancelled ones become monitor).
    """
    actions = actions.copy()
    n = len(actions)
    cap = max(1, math.floor(max_fraction * n))
    already = int((status == 2).sum() - ((status == 2) & (actions == RECONNECT)).sum())
    want = np.where((actions == ISOLATE) & (status != 2))[0]
    room = max(0, cap - already)
    if len(want) > room:
        keep = want[np.argsort(-risk[want])[:room]]
        for i in want:
            if i not in keep:
                actions[i] = MONITOR
    return actions


@dataclass
class Guardrails:
    max_isolated_fraction: float = 0.5
    min_confidence_to_isolate: float = 0.6
    min_risk_to_isolate: float = 0.5
    critical_nodes: set[str] = field(default_factory=set)
    max_isolations_per_minute: int = 5
    enabled: bool = True
    _recent: list[float] = field(default_factory=list, repr=False)

    def check(self, action: str, s1: dict, status: dict[str, str], now: float | None = None) -> tuple[str, bool, str]:
        """Return (final_action, requires_human_approval, reason)."""
        now = time.time() if now is None else now
        node = s1["node_id"]
        if not self.enabled:
            return "monitor", False, "kill_switch: agent disabled, monitoring only"
        if action not in ACTIONS:
            return "monitor", False, f"allowlist: '{action}' is not an allowed action"
        cur = status.get(node, ONLINE)
        if action == "isolate":
            if cur == ISOLATED:
                return "monitor", False, "already isolated"
            if s1["threat_label"] == "BENIGN" or s1["confidence"] < self.min_confidence_to_isolate \
                    or s1["risk_score_node"] < self.min_risk_to_isolate:
                return "monitor", False, "evidence: not enough proof to isolate, watching instead"
            known = max(len(status), 1)
            n_iso = sum(1 for v in status.values() if v == ISOLATED)
            if n_iso + 1 > max(1, math.floor(self.max_isolated_fraction * known)):
                return "monitor", False, f"blast_radius: {n_iso} of {known} nodes already isolated"
            self._recent = [t for t in self._recent if now - t < 60]
            if node in self.critical_nodes:
                return "isolate", True, "critical node: human approval required"
            if len(self._recent) >= self.max_isolations_per_minute:
                return "isolate", True, "rate_limit: too many isolations this minute, human approval required"
        if action == "reconnect" and cur != ISOLATED:
            return "monitor", False, "node is not isolated"
        return action, False, "ok"

    def record_isolation(self, now: float | None = None) -> None:
        self._recent.append(time.time() if now is None else now)
