"""Build results/jarvis_dashboard.html from REAL Stage 2 runs.

    python -m visualization.build_jarvis

It runs the real Stage 2 code (BB84, ML-KEM, ML-DSA, signed commands, AES-GCM) for every
scenario, records the numbers, and bakes them into one self-contained HTML file.
Double-click the HTML file to open it. No server, no internet needed.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import platform
import time

from cryptography.exceptions import InvalidTag

from stage2 import pqc
from stage2.bb84 import THRESHOLD, bb84
from stage2.channel import decrypt, derive_session_key, encrypt
from stage2.commands import CommandSigner, CommandVerifier
from stage2.pipeline import secure_channel

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "jarvis_dashboard.html"
NODE, N_SHOW, N_QUBITS = "192.168.1.14", 16, 1024


def bb84_view(eve: float, seed0: int) -> dict:
    """One BB84 run; pick a seed whose first 16 qubits tell the story (errors visible if Eve is on)."""
    for seed in range(seed0, seed0 + 500):
        r = bb84(N_QUBITS, eve_fraction=eve, seed=seed)
        d = r.details
        m = d["alice_bases"][:N_SHOW] == d["bob_bases"][:N_SHOW]
        errs = int(((d["alice_bits"][:N_SHOW] != d["bob_bits"][:N_SHOW]) & m).sum())
        if (eve == 0 and errs == 0) or (eve > 0 and errs >= 2):
            break
    cells = [{"a": int(d["alice_bits"][i]), "ab": int(d["alice_bases"][i]), "bb": int(d["bob_bases"][i]),
              "r": int(d["bob_bits"][i]), "e": bool(d["intercepted"][i])} for i in range(N_SHOW)]
    return {"cells": cells, "qber": round(r.qber, 4), "n": N_QUBITS, "sifted": r.sifted_len,
            "tested": r.test_len, "detected": r.eavesdrop_detected}


def slim(s2: dict) -> dict:
    keep = {k: s2[k] for k in ("status", "qber", "key_gen_time_ms", "timings_ms", "sizes_bytes") if k in s2}
    keep["key_id"] = s2.get("shared_key_id", "").split("_")[-1] or None
    return keep


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return out, round((time.perf_counter() - t) * 1000, 1)


def collect() -> dict:
    clean, eve, heal = secure_channel(NODE, seed=11), secure_channel(NODE, eve_fraction=1.0, seed=12), secure_channel(NODE, seed=13)
    signer = CommandSigner()
    ver = CommandVerifier(signer.public_key)

    iso, sign_ms = timed(lambda: signer.sign(NODE, "isolate"))
    ok_iso, verify_ms = timed(lambda: ver.verify(iso))
    replay = ver.verify(iso)
    forged = signer.sign(NODE, "isolate")
    forged["payload"]["action"] = "reconnect"
    cmd = {
        "isolate": {"verify": list(ok_iso), "sig_bytes": len(bytes.fromhex(iso["signature"])), "sign_ms": sign_ms,
                    "verify_ms": verify_ms, "nonce": iso["payload"]["nonce"][:8]},
        "replay": list(replay), "forged": list(ver.verify(forged)),
        "stale": list(CommandVerifier(signer.public_key).verify(signer.sign(NODE, "isolate", now=1.0))),
        "bad_action": list(CommandVerifier(signer.public_key).verify(signer.sign(NODE, "format_disk"))),
        "attacker": list(CommandVerifier(signer.public_key).verify(CommandSigner().sign(NODE, "reconnect"))),
        "reconnect": list(ver.verify(signer.sign(NODE, "reconnect"))),
    }
    key = derive_session_key(b"a" * 32, b"b" * 32, b"n")
    blob = encrypt(key, b"traffic", b"n")
    try:
        decrypt(key, blob[:-1] + bytes([blob[-1] ^ 1]), b"n")
        aes = "ACCEPTED (bug)"
    except InvalidTag:
        aes = "InvalidTag"
    ek, dk = pqc.kem_keygen()
    ss, ct = pqc.kem_encaps(ek)
    kem_differs = pqc.kem_decaps(dk, bytes([ct[0] ^ 1]) + ct[1:]) != ss

    import qiskit
    return {
        "meta": {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                 "machine": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}, Qiskit {qiskit.__version__}",
                 "threshold": THRESHOLD, "node": NODE},
        "clean": {"s2": slim(clean), "bb84": bb84_view(0.0, 100)},
        "eve": {"s2": slim(eve), "bb84": bb84_view(1.0, 200)},
        "heal": {"s2": slim(heal), "bb84": bb84_view(0.0, 300)},
        "cmd": cmd, "traffic": {"aes_tamper": aes, "kem_tamper_differs": bool(kem_differs)},
    }


def main() -> None:
    data = collect()
    html = (HERE / "jarvis_template.html").read_text().replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html)
    print(f"Wrote {OUT}  ({len(html) // 1024} KB). Open it in any browser.")
    print("clean:", data["clean"]["s2"]["status"], "| eve:", data["eve"]["s2"]["status"], "| forged:", data["cmd"]["forged"])


if __name__ == "__main__":
    main()
