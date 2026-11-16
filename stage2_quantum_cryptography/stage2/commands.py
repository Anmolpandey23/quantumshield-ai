"""Signed commands for Stage 3 (isolate / monitor / reconnect).

Every command is signed with ML-DSA. The verifier rejects:
  - forged or edited commands   (bad signature)
  - actions outside the allowlist (guardrail)
  - old commands                (stale timestamp)
  - re-sent commands            (replay: nonce already seen)
"""
from __future__ import annotations

import json
import os
import time

from . import pqc

ALLOWED_ACTIONS = {"isolate", "monitor", "reconnect"}


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class CommandSigner:
    def __init__(self) -> None:
        self.public_key, self._secret_key = pqc.sig_keygen()

    def sign(self, node_id: str, action: str, now: float | None = None) -> dict:
        payload = {"node_id": node_id, "action": action,
                   "issued_at": time.time() if now is None else now,
                   "nonce": os.urandom(16).hex()}
        return {"payload": payload, "signature": pqc.sign(self._secret_key, _canonical(payload)).hex()}


class CommandVerifier:
    def __init__(self, public_key: bytes, max_age_s: float = 30.0) -> None:
        self.public_key = public_key
        self.max_age_s = max_age_s
        self._seen: set[str] = set()

    def verify(self, signed: dict, now: float | None = None) -> tuple[bool, str]:
        now = time.time() if now is None else now
        try:
            payload, sig = signed["payload"], bytes.fromhex(signed["signature"])
        except (KeyError, ValueError, TypeError):
            return False, "malformed_command"
        if not pqc.verify(self.public_key, _canonical(payload), sig):
            return False, "bad_signature"
        if payload.get("action") not in ALLOWED_ACTIONS:
            return False, "action_not_allowed"
        if abs(now - payload.get("issued_at", 0)) > self.max_age_s:
            return False, "stale_command"
        if payload.get("nonce") in self._seen:
            return False, "replay_detected"
        self._seen.add(payload["nonce"])
        return True, "ok"
