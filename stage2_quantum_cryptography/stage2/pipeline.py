"""Stage 2 pipeline: QRNG -> BB84 -> ML-KEM -> hybrid key + AES-GCM -> ML-DSA."""
from __future__ import annotations

import json
import time

from . import pqc
from .bb84 import bb84
from .channel import decrypt, derive_session_key, encrypt
from .qrng import qrng_bytes


def secure_channel(node_id: str, stage1_output: dict | None = None, *, n_qubits: int = 2048,
                   eve_fraction: float = 0.0, channel_error: float = 0.0,
                   seed: int | None = None) -> dict:
    """Establish a quantum-safe channel for `node_id`. Returns the Stage 2 output contract."""
    timings: dict[str, float] = {}
    t_start = time.perf_counter()

    def lap(name: str, t0: float) -> float:
        timings[name] = round((time.perf_counter() - t0) * 1000, 2)
        return time.perf_counter()

    t = time.perf_counter()
    qrng_seed = qrng_bytes(32, seed)                       # 1. quantum random seed
    pqc.seed_from_qrng(qrng_seed)                          #    seeds the PQC key generators
    t = lap("qrng_ms", t)

    bb = bb84(n_qubits=n_qubits, eve_fraction=eve_fraction, channel_error=channel_error,
              seed=None if seed is None else seed + 1)     # 2. BB84 key agreement
    t = lap("bb84_ms", t)
    if bb.reason != "ok" or not bb.keys_match:
        status = ("aborted_eavesdrop_detected" if bb.eavesdrop_detected
                  else "aborted_insufficient_key_material" if bb.reason == "insufficient_key_material"
                  else "aborted_key_mismatch")
        return {"node_id": node_id, "status": status, "eavesdrop_detected": bb.eavesdrop_detected,
                "qber": round(bb.qber, 4), "reason": bb.reason,
                "key_gen_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
                "timings_ms": timings}

    ek, dk = pqc.kem_keygen()                              # 3. ML-KEM key establishment
    ss_sender, ct = pqc.kem_encaps(ek)
    ss_receiver = pqc.kem_decaps(dk, ct)
    t = lap("ml_kem_ms", t)

    ctx = node_id.encode()                                 # 4. hybrid session key + AES-256-GCM
    key_sender = derive_session_key(ss_sender, bb.key_alice, ctx)
    key_receiver = derive_session_key(ss_receiver, bb.key_bob, ctx)
    probe = b"stage2 traffic check"
    traffic_ok = decrypt(key_receiver, encrypt(key_sender, probe, ctx), ctx) == probe
    t = lap("hkdf_aes_ms", t)

    sig_pk, sig_sk = pqc.sig_keygen()                      # 5. ML-DSA signed event
    event = json.dumps({"node_id": node_id, "event": "channel_established",
                        "qber": round(bb.qber, 4)}, sort_keys=True).encode()
    signature = pqc.sign(sig_sk, event)
    sig_ok = pqc.verify(sig_pk, event, signature)
    t = lap("ml_dsa_ms", t)

    ok = traffic_ok and sig_ok and ss_sender == ss_receiver and key_sender == key_receiver
    return {
        "node_id": node_id,
        "key_generation_method": "QRNG+BB84+ML-KEM-768 (hybrid HKDF)",
        "shared_key_id": f"key_{node_id}_{key_sender.hex()[:8]}",
        "kem_ciphertext": ct.hex(),
        "signature_public_key": sig_pk.hex(),
        "signature": signature.hex(),
        "eavesdrop_detected": False,
        "qber": round(bb.qber, 4),
        "key_gen_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        "timings_ms": timings,
        "sizes_bytes": {"kem_public_key": len(ek), "kem_ciphertext": len(ct),
                        "sig_public_key": len(sig_pk), "signature": len(signature)},
        "status": "secure_channel_established" if ok else "failed_self_check",
    }
