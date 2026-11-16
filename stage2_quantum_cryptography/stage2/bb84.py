"""BB84 quantum key distribution, simulated with Qiskit (stabilizer simulator).

Roles: Alice sends qubits, Bob measures them, Eve optionally intercepts.
Eve uses the classic intercept-resend attack: she measures in a random basis
and resends what she saw. This disturbs ~25% of the sifted bits she touches.

Both circuits are batched (one qubit per transmitted bit), so a run needs only
two simulator calls. Everything quantum is really simulated, including Eve's
measurements.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit

from .qrng import measure_bits

THRESHOLD = 0.11   # abort if estimated QBER is above ~11% (BB84 security limit)
MIN_RAW_KEY = 128  # minimum raw key bits needed after sifting and testing


@dataclass
class BB84Result:
    n_qubits: int
    sifted_len: int
    test_len: int
    raw_key_len: int
    qber: float
    threshold: float
    eavesdrop_detected: bool
    reason: str                 # "ok" | "qber_above_threshold" | "insufficient_key_material"
    keys_match: bool
    key_alice: bytes | None
    key_bob: bytes | None
    eve_fraction: float
    channel_error: float
    details: dict = field(default_factory=dict, repr=False)

    def summary(self) -> dict:
        return {
            "n_qubits": self.n_qubits, "sifted_len": self.sifted_len,
            "test_len": self.test_len, "raw_key_len": self.raw_key_len,
            "qber": round(self.qber, 4), "threshold": self.threshold,
            "eavesdrop_detected": self.eavesdrop_detected, "reason": self.reason,
            "keys_match": self.keys_match,
            "eve_fraction": self.eve_fraction, "channel_error": self.channel_error,
        }


def _prepare(qc: QuantumCircuit, q: int, bit: int, basis: int) -> None:
    """Encode `bit` in `basis` (0 = Z basis '+', 1 = X basis 'x')."""
    if bit:
        qc.x(q)
    if basis:
        qc.h(q)


def privacy_amplify(bits: np.ndarray) -> bytes:
    """Compress the raw key into a 256-bit key with SHA-256 (simple privacy amplification)."""
    return hashlib.sha256(np.packbits(bits).tobytes()).digest()


def bb84(n_qubits: int = 2048, eve_fraction: float = 0.0, channel_error: float = 0.0,
         threshold: float = THRESHOLD, test_fraction: float = 0.25,
         seed: int | None = None) -> BB84Result:
    """Run one BB84 session.

    eve_fraction  : share of qubits Eve intercepts (0 = no eavesdropper, 1 = all)
    channel_error : probability that Bob's detector flips a bit (honest noise)
    test_fraction : share of sifted bits revealed to estimate QBER
    """
    rng = np.random.default_rng(seed)
    n = n_qubits
    alice_bits = rng.integers(0, 2, n)
    alice_bases = rng.integers(0, 2, n)
    bob_bases = rng.integers(0, 2, n)
    intercepted = rng.random(n) < eve_fraction
    eve_bases = rng.integers(0, 2, n)

    def sim_seed() -> int:
        return int(rng.integers(0, 2**31 - 1))

    # Circuit 1: Alice prepares; Eve measures the qubits she intercepts.
    eve_bits = np.zeros(n, dtype=np.uint8)
    if intercepted.any():
        qc1 = QuantumCircuit(n, n)
        for q in range(n):
            _prepare(qc1, q, int(alice_bits[q]), int(alice_bases[q]))
            if intercepted[q]:
                if eve_bases[q]:
                    qc1.h(q)
                qc1.measure(q, q)
        eve_bits = measure_bits(qc1, sim_seed())

    # Circuit 2: qubits travel to Bob (Eve re-prepares what she measured), Bob measures.
    qc2 = QuantumCircuit(n, n)
    for q in range(n):
        if intercepted[q]:
            _prepare(qc2, q, int(eve_bits[q]), int(eve_bases[q]))
        else:
            _prepare(qc2, q, int(alice_bits[q]), int(alice_bases[q]))
        if bob_bases[q]:
            qc2.h(q)
        qc2.measure(q, q)
    bob_bits = measure_bits(qc2, sim_seed())
    if channel_error > 0:
        bob_bits = bob_bits ^ (rng.random(n) < channel_error).astype(np.uint8)

    # Sifting: keep positions where Alice's and Bob's bases matched.
    matched = np.flatnonzero(alice_bases == bob_bases)
    perm = rng.permutation(matched)
    n_test = max(1, int(round(len(matched) * test_fraction))) if len(matched) else 0
    test_idx, key_idx = perm[:n_test], np.sort(perm[n_test:])

    qber = float(np.mean(alice_bits[test_idx] != bob_bits[test_idx])) if n_test else 1.0
    if qber > threshold:
        reason = "qber_above_threshold"
    elif len(key_idx) < MIN_RAW_KEY:
        reason = "insufficient_key_material"
    else:
        reason = "ok"
    abort = reason != "ok"

    ka, kb = alice_bits[key_idx].astype(np.uint8), bob_bits[key_idx].astype(np.uint8)
    keys_match = bool(np.array_equal(ka, kb)) and not abort
    return BB84Result(
        n_qubits=n, sifted_len=len(matched), test_len=n_test, raw_key_len=len(key_idx),
        qber=qber, threshold=threshold, eavesdrop_detected=(reason == "qber_above_threshold"),
        reason=reason, keys_match=keys_match,
        key_alice=None if abort else privacy_amplify(ka),
        key_bob=None if abort else privacy_amplify(kb),
        eve_fraction=eve_fraction, channel_error=channel_error,
        details={"alice_bits": alice_bits, "alice_bases": alice_bases, "bob_bases": bob_bases,
                 "bob_bits": bob_bits, "intercepted": intercepted, "test_idx": test_idx,
                 "key_idx": key_idx},
    )
