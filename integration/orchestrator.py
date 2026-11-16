"""The Stage 1 -> Stage 2 -> Stage 3 -> Stage 4 flow for one node.

Real code from Stage 2 is used here (secure_channel, CommandSigner, CommandVerifier).
Stage 1 and Stage 3 come from `stubs.py` unless you pass the real ones (see `integration/live.py`).

Life of a node:  online -> (threat) -> isolated -> (looks clean, new keys) -> online
Rules that always hold:
  * no command is ever sent over a channel Stage 2 could not secure (eavesdropper => abort),
  * every command is ML-DSA signed and verified before it is applied,
  * drastic actions the guardrails mark as critical wait for a human (`approve()` / `reject()`).
"""
from __future__ import annotations

import itertools
import threading
from datetime import datetime, timezone
from typing import Callable

from stage2.commands import CommandSigner, CommandVerifier
from stage2.pipeline import secure_channel

from .stubs import stage3_policy_stub
from .validate import validate

TRIGGER = 0.6            # Stage 2 starts only when Stage 1 flags a threat at or above this score
RECONNECT_RISK = 0.3     # an isolated node is considered for reconnection once its risk is below this


class Orchestrator:
    def __init__(self, policy: Callable[[dict, dict], str] = stage3_policy_stub, n_qubits: int = 1024,
                 fleet=None) -> None:
        self.policy, self.n_qubits, self.fleet = policy, n_qubits, fleet
        self.signer = CommandSigner()                              # controller's ML-DSA key
        self.verifier = CommandVerifier(self.signer.public_key)   # controller-side check before acting
        self.status: dict[str, str] = {}                           # node_id -> online | monitored | isolated
        self.node_keys: dict[str, str] = {}                        # node_id -> current shared_key_id
        self.pending: dict[str, dict] = {}                         # approval_id -> waiting decision
        self._ids = itertools.count(1)
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ helpers
    def _base_event(self, s1: dict) -> dict:
        return {"contract_version": "1.0", "timestamp": datetime.now(timezone.utc).isoformat(),
                "node_id": s1["node_id"], "decision": "no_action", "stage1": s1,
                "stage2": None, "stage3_command": None, "command_verified": None,
                "node_status": self.status.get(s1["node_id"], "online")}

    def _decide(self, s1: dict, s2: dict, recovering: bool) -> dict:
        if hasattr(self.policy, "decide"):
            return self.policy.decide(s1, s2)
        action = self.policy(s1, s2)
        if recovering and action == "monitor":                       # stub policy has no memory: simple recovery rule
            action = "reconnect"
        return {"action": action, "requires_approval": False, "reason": "stub policy", "source": "stub", "proposed": action}

    def _issue(self, event: dict, s1: dict, s2: dict, action: str) -> dict:
        node = s1["node_id"]
        command = validate(self.signer.sign(node, action), "stage3_command")
        ok, _reason = self.verifier.verify(command)
        applied = None
        if ok and self.fleet is not None:                            # node-side check: the machine verifies on its own
            applied, _ = self.fleet.apply(command)
            ok = ok and applied
        event.update(stage3_command=command, command_verified=ok, node_applied=applied,
                     decision="command_issued" if ok else "command_rejected")
        if ok:
            self.status[node] = ({"isolate": "isolated", "reconnect": "online"}.get(action)
                                 or ("monitored" if self.status.get(node) != "isolated" else "isolated"))
            if action == "isolate":
                self.node_keys.pop(node, None)                       # revoke: an isolated node holds no valid session key
            elif action == "reconnect":
                self.node_keys[node] = s2["shared_key_id"]           # fresh QRNG+BB84+ML-KEM key from THIS handshake
                event["rekeyed"] = True
            if hasattr(self.policy, "on_applied"):
                self.policy.on_applied(node, action)
        event["node_status"] = self.status.get(node, "online")
        return event

    # ------------------------------------------------------------------ main entry
    def handle(self, stage1_output: dict, *, eve_fraction: float = 0.0, seed: int | None = None) -> dict:
        with self._lock:
            s1 = validate(stage1_output, "stage1_output")
            node = s1["node_id"]
            if hasattr(self.policy, "observe"):
                self.policy.observe(s1)
            event = self._base_event(s1)
            cur = self.status.get(node, "online")

            flagged = s1["threat_label"] != "BENIGN" and max(s1["confidence"], s1["anomaly_score"]) >= TRIGGER
            recovering = cur == "isolated" and not flagged and s1["risk_score_node"] < RECONNECT_RISK
            if not (flagged or recovering):
                return validate(event, "pipeline_event")

            s2 = validate(secure_channel(node, s1, n_qubits=self.n_qubits, eve_fraction=eve_fraction, seed=seed),
                          "stage2_output")
            event["stage2"] = s2
            if s2["status"] != "secure_channel_established":
                event["decision"] = "aborted_no_command"             # never act over an untrusted channel
                return validate(event, "pipeline_event")

            d = self._decide(s1, s2, recovering)
            event["policy"] = d
            if cur == "isolated" and d["action"] == "monitor" and not d["requires_approval"]:
                event["policy"] = {**d, "reason": "holding in quarantine until clean for longer"}
                return validate(event, "pipeline_event")            # nothing to sign: it simply stays isolated
            if d["requires_approval"]:
                aid = f"apr_{next(self._ids)}"
                self.pending[aid] = {"approval_id": aid, "node_id": node, "action": d["action"], "reason": d["reason"],
                                     "s1": s1, "s2": s2, "created": event["timestamp"]}
                event.update(decision="pending_human_approval",
                             pending_approval={k: self.pending[aid][k] for k in ("approval_id", "node_id", "action", "reason")})
                return validate(event, "pipeline_event")
            return validate(self._issue(event, s1, s2, d["action"]), "pipeline_event")

    # ------------------------------------------------------------------ human in the loop
    def list_pending(self) -> list[dict]:
        with self._lock:
            return [{k: v[k] for k in ("approval_id", "node_id", "action", "reason", "created")} for v in self.pending.values()]

    def approve(self, approval_id: str, approver: str = "operator") -> dict:
        with self._lock:
            item = self.pending.pop(approval_id)                     # KeyError if unknown: caller turns it into a 404
            event = self._base_event(item["s1"])
            event.update(stage2=item["s2"], policy={"action": item["action"], "requires_approval": True,
                                                    "reason": f"approved by {approver}", "source": "human", "proposed": item["action"]})
            return validate(self._issue(event, item["s1"], item["s2"], item["action"]), "pipeline_event")

    def reject(self, approval_id: str, approver: str = "operator") -> dict:
        with self._lock:
            item = self.pending.pop(approval_id)
            event = self._base_event(item["s1"])
            event.update(stage2=item["s2"], decision="command_rejected",
                         policy={"action": "monitor", "requires_approval": True, "reason": f"rejected by {approver}",
                                 "source": "human", "proposed": item["action"]})
            return validate(event, "pipeline_event")
