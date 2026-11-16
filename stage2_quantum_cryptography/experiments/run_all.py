"""Run every Stage 2 experiment and write figures, CSV files and RESULTS.md.

    python -m experiments.run_all           # full run (about 5 minutes)
    python -m experiments.run_all --quick   # fewer trials (about 1 minute)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import statistics as st
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, x25519

from stage2 import pqc
from stage2.bb84 import THRESHOLD, bb84
from stage2.channel import decrypt, derive_session_key, encrypt
from stage2.commands import CommandSigner, CommandVerifier
from stage2.pipeline import secure_channel
from stage2.qrng import qrng_bits

PUR, TEAL, ORG, GOLD, DARK, LAV = "#7E48D6", "#0F8A64", "#D9622B", "#B8860B", "#1B0F2E", "#5B4B7A"
OUT = Path("results")
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 150, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.labelsize": 10, "font.size": 9})
SUMMARY: dict = {}


def save(fig, name: str, tight: bool = True) -> None:
    if tight:
        fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved", name)


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ---------------------------------------------------------------- fig 0: architecture
def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 4.2))
    ax.axis("off"); ax.set_xlim(0, 12.5); ax.set_ylim(0, 4.2)
    boxes = [("Stage 1\ninput", "node, threat,\nconfidence", LAV), ("QRNG", "Hadamard +\nmeasure", PUR),
             ("BB84", "sift, test QBER,\nabort > 11%", ORG), ("ML-KEM-768", "encapsulate /\ndecapsulate", TEAL),
             ("HKDF +\nAES-256-GCM", "hybrid session key,\nencrypt traffic", GOLD),
             ("ML-DSA-65", "sign events\nand commands", PUR), ("Stage 3\noutput", "key id, QBER,\nstatus, timings", LAV)]
    w, gap = 1.5, 0.33
    for i, (title, sub, col) in enumerate(boxes):
        x = 0.2 + i * (w + gap)
        ax.add_patch(plt.Rectangle((x, 1.5), w, 1.7, color=col, alpha=0.12, lw=0))
        ax.add_patch(plt.Rectangle((x, 3.0), w, 0.2, color=col, lw=0))
        ax.text(x + w / 2, 2.62, title, ha="center", va="center", fontweight="bold", fontsize=10, color=DARK)
        ax.text(x + w / 2, 1.95, sub, ha="center", va="center", fontsize=8, color=LAV)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(x + w + gap - 0.04, 2.35), xytext=(x + w + 0.04, 2.35),
                        arrowprops=dict(arrowstyle="-|>", color=DARK, lw=1.4))
    ax.annotate("", xy=(0.2 + 3 * (w + gap) + w / 2, 1.45), xytext=(0.2 + 1 * (w + gap) + w / 2, 1.45),
                arrowprops=dict(arrowstyle="-|>", color=PUR, lw=1.4, connectionstyle="arc3,rad=0.35"))
    ax.text(0.2 + 2 * (w + gap) + w / 2, 0.55, "QRNG bytes seed the ML-KEM and ML-DSA key generators",
            ha="center", fontsize=9, color=PUR, fontweight="bold")
    ax.text(6.25, 4.0, "Stage 2: Quantum-Safe Cryptography pipeline", ha="center", fontsize=13,
            fontweight="bold", color=DARK)
    ax.text(0.2 + 2 * (w + gap) + w / 2, 0.15, "Eavesdropper found: stop, no key is used", ha="center",
            fontsize=8.5, color=ORG)
    save(fig, "fig0_architecture.png")


# ---------------------------------------------------------------- fig 1: QRNG quality
def fig_qrng(n_bytes: int) -> dict:
    bits = qrng_bits(8 * n_bytes)
    data = np.packbits(bits)
    n = len(bits)
    s = 2 * int(bits.sum()) - n
    p_mono = math.erfc(abs(s) / math.sqrt(2 * n))
    counts = np.bincount(data, minlength=256)
    chi2 = float(((counts - n_bytes / 256) ** 2 / (n_bytes / 256)).sum())
    z_chi = (chi2 - 255) / math.sqrt(2 * 255)
    x = 2.0 * bits - 1
    r1 = float(np.mean(x[:-1] * x[1:]))
    tests = [("Monobit (bit balance)", f"p = {p_mono:.3f}", p_mono > 0.01),
             ("Byte chi-square (255 df)", f"z = {z_chi:+.2f}", abs(z_chi) < 3),
             ("Serial correlation (lag 1)", f"r = {r1:+.4f}", abs(r1) < 4 / math.sqrt(n))]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].bar(range(256), counts, color=PUR, width=1.0)
    ax[0, 0].axhline(n_bytes / 256, color=ORG, ls="--", label="expected if uniform")
    ax[0, 0].set(title=f"Byte values from {n_bytes:,} QRNG bytes", xlabel="byte value", ylabel="count")
    ax[0, 0].legend(frameon=False)
    ax[0, 1].imshow(bits[:64 * 128].reshape(64, 128), cmap="Purples", interpolation="nearest", aspect="auto")
    ax[0, 1].set(title="First 8,192 random bits (dark = 1)"); ax[0, 1].grid(False); ax[0, 1].set_xticks([]); ax[0, 1].set_yticks([])
    run = np.cumsum(bits) / np.arange(1, n + 1)
    ax[1, 0].plot(np.arange(1, n + 1), run, color=TEAL, lw=1)
    ax[1, 0].axhline(0.5, color=ORG, ls="--")
    ax[1, 0].set(title="Running share of ones converges to 0.5", xlabel="bits generated", ylabel="share of ones",
                 xscale="log", ylim=(0.3, 0.7))
    ax[1, 1].axis("off")
    for i, (name, val, ok) in enumerate(tests):
        y = 0.82 - i * 0.24
        ax[1, 1].add_patch(plt.Rectangle((0.02, y - 0.09), 0.96, 0.18, color=TEAL if ok else ORG, alpha=0.14, lw=0))
        ax[1, 1].text(0.05, y, name, fontweight="bold", va="center", color=DARK)
        ax[1, 1].text(0.62, y, val, va="center", color=LAV)
        ax[1, 1].text(0.93, y, "PASS" if ok else "FAIL", va="center", ha="right", fontweight="bold", color=TEAL if ok else ORG)
    ax[1, 1].set(title="Basic randomness checks", xlim=(0, 1), ylim=(0, 1))
    fig.suptitle("QRNG output quality (simulated; real randomness needs real hardware)", fontweight="bold", y=1.0)
    save(fig, "fig1_qrng_quality.png")
    return {"bytes": n_bytes, "monobit_p": round(p_mono, 4), "chi2_z": round(z_chi, 3),
            "serial_r": round(r1, 5), "all_pass": all(t[2] for t in tests)}


# ---------------------------------------------------------------- fig 2: BB84 walkthrough
def _table(ax, rows, cells, colors, title):
    ncol = len(cells[0])
    ax.set_xlim(-2.6, ncol); ax.set_ylim(-len(rows), 0.4); ax.axis("off"); ax.set_title(title, loc="left")
    for r, label in enumerate(rows):
        ax.text(-2.5, -r - 0.5, label, va="center", fontsize=8, fontweight="bold", color=DARK)
        for c in range(ncol):
            ax.add_patch(plt.Rectangle((c, -r - 1), 0.96, 0.9, color=colors[r][c], alpha=0.85, lw=0))
            ax.text(c + 0.48, -r - 0.5, cells[r][c], ha="center", va="center", fontsize=8, color=DARK)


def fig_bb84_walkthrough() -> None:
    n = 16
    pick = {}
    for eve in (0.0, 1.0):
        for seed in range(500):
            r = bb84(n, eve_fraction=eve, seed=seed, test_fraction=0.34)
            d = r.details
            m = d["alice_bases"] == d["bob_bases"]
            errs = int((d["alice_bits"][m] != d["bob_bits"][m]).sum())
            if r.test_len >= 2 and ((eve == 0.0) or (errs >= 2 and errs <= 3)):
                pick[eve] = r; break
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.2))
    for ax, eve in zip(axes, (0.0, 1.0)):
        r = pick[eve]; d = r.details
        basis = lambda b: "x" if b else "+"
        match = d["alice_bases"] == d["bob_bases"]
        rows = ["Alice bit", "Alice basis", "Bob basis", "Bob result", "Bases match?", "Role"]
        cells, cols = [[] for _ in rows], [[] for _ in rows]
        for q in range(n):
            role, rc = ("discarded", "#DDDDDD")
            if match[q]:
                if q in set(d["test_idx"]):
                    bad = d["alice_bits"][q] != d["bob_bits"][q]
                    role, rc = ("test: ERROR", ORG) if bad else ("test: ok", GOLD)
                else:
                    role, rc = "key bit", TEAL
            vals = [(int(d["alice_bits"][q]), "#E6DCF7"), (basis(d["alice_bases"][q]), "#E6DCF7"),
                    (basis(d["bob_bases"][q]), "#F3EFFA"), (int(d["bob_bits"][q]), "#F3EFFA"),
                    ("yes" if match[q] else "no", "#E6F4EE" if match[q] else "#EEEEEE"), (role.replace("test: ", "t:"), rc)]
            for i, (v, c) in enumerate(vals):
                cells[i].append(str(v)); cols[i].append(c)
        t = ("Clean channel" if eve == 0 else "Eavesdropper intercepts every qubit")
        _table(ax, rows, cells, cols, f"{t}: QBER measured on the test bits = {r.qber:.0%}"
                                         + ("   (no errors)" if eve == 0 else "   (Eve disturbed some matching-basis bits)"))
    fig.suptitle("BB84 step by step on 16 qubits (key bit = used for the key, t: = revealed to estimate QBER)",
                 fontweight="bold")
    save(fig, "fig2_bb84_walkthrough.png")


# ---------------------------------------------------------------- fig 3: QBER sweeps
def fig_qber(trials: int, n: int) -> dict:
    fr = np.round(np.linspace(0, 1, 11), 2)
    eve_rows, eve_stats = [], []
    for f in fr:
        res = [bb84(n, eve_fraction=float(f), seed=1000 + i) for i in range(trials)]
        q = [r.qber for r in res]
        eve_stats.append((f, np.mean(q), np.std(q), np.mean([r.eavesdrop_detected for r in res])))
        eve_rows += [[f, i, round(x, 4)] for i, x in enumerate(q)]
    write_csv("data_qber_vs_eve.csv", ["eve_fraction", "trial", "qber"], eve_rows)
    ps = np.round(np.linspace(0, 0.2, 11), 3)
    noise_stats = []
    for p in ps:
        q = [bb84(n, channel_error=float(p), seed=5000 + i).qber for i in range(trials)]
        noise_stats.append((p, np.mean(q), np.std(q)))
    write_csv("data_qber_vs_noise.csv", ["channel_error", "mean_qber", "std_qber"],
              [[round(a, 3), round(b, 4), round(c, 4)] for a, b, c in noise_stats])
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    f, m, s, d = zip(*eve_stats)
    ax[0].errorbar(f, m, yerr=s, fmt="o-", color=PUR, capsize=3, label="measured (simulated)")
    ax[0].plot(fr, 0.25 * fr, "--", color=GOLD, label="theory: 25% x fraction")
    ax[0].axhline(THRESHOLD, color=ORG, ls=":", label="abort threshold 11%")
    ax[0].set(title="QBER grows with eavesdropping", xlabel="fraction of qubits Eve intercepts", ylabel="QBER")
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].bar([str(int(x * 100)) + "%" for x in f], d, color=[TEAL if v < 0.5 else ORG for v in d])
    ax[1].set(title="Share of runs flagged by the 11% rule", xlabel="fraction of qubits Eve intercepts",
              ylabel="runs aborted", ylim=(0, 1.05))
    ax[1].tick_params(axis="x", labelsize=7)
    p, m2, s2 = zip(*noise_stats)
    ax[2].errorbar(p, m2, yerr=s2, fmt="o-", color=TEAL, capsize=3, label="measured")
    ax[2].plot(ps, ps, "--", color=GOLD, label="theory: QBER = noise")
    ax[2].axhline(THRESHOLD, color=ORG, ls=":", label="abort threshold 11%")
    ax[2].set(title="Honest noise also raises QBER", xlabel="detector error probability", ylabel="QBER")
    ax[2].legend(frameon=False, fontsize=8)
    fig.suptitle(f"BB84 error-rate experiments ({trials} runs per point, {n} qubits per run)", fontweight="bold", y=1.03)
    save(fig, "fig3_qber_experiments.png")
    full = [x for x in eve_stats if x[0] == 1.0][0]
    return {"clean_qber_mean": round(float(eve_stats[0][1]), 4), "eve_full_qber_mean": round(float(full[1]), 4),
            "eve_full_detect_rate": round(float(full[3]), 4), "trials_per_point": trials, "qubits_per_run": n}


# ---------------------------------------------------------------- fig 4: detection vs qubits
def fig_detection(trials: int) -> dict:
    ns = [16, 32, 64, 128, 256, 512]
    det, fa = [], []
    for n in ns:
        det.append(np.mean([bb84(n, eve_fraction=1.0, channel_error=0.02, seed=i).qber > THRESHOLD for i in range(trials)]))
        fa.append(np.mean([bb84(n, channel_error=0.02, seed=9000 + i).qber > THRESHOLD for i in range(trials)]))
    write_csv("data_detection_vs_qubits.csv", ["n_qubits", "detection_rate", "false_alarm_rate"],
              [[a, round(b, 3), round(c, 3)] for a, b, c in zip(ns, det, fa)])
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(ns, det, "o-", color=TEAL, label="eavesdropper detected")
    ax.plot(ns, fa, "s-", color=ORG, label="false alarm (no eavesdropper)")
    ax.set(xscale="log", xlabel="qubits sent", ylabel="rate", ylim=(-0.02, 1.05),
           title=f"More qubits = more reliable test ({trials} runs, 2% honest noise)")
    ax.set_xticks(ns); ax.set_xticklabels(ns); ax.legend(frameon=False)
    save(fig, "fig4_detection_vs_qubits.png")
    return {"detection_rate_by_qubits": dict(zip(map(str, ns), map(lambda v: round(float(v), 3), det)))}


# ---------------------------------------------------------------- fig 5: sizes
def fig_sizes() -> dict:
    xk = x25519.X25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    edk = ed25519.Ed25519PrivateKey.generate()
    rk = rsa.generate_private_key(65537, 2048)
    rpk = rk.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    pk, sk = pqc.sig_keygen(); sig = pqc.sign(sk, b"m")
    sizes = {"X25519 key share": len(xk), "ML-KEM-768 public key": len(ek), "ML-KEM-768 ciphertext": len(ct),
             "ML-KEM-768 secret key": len(dk), "Ed25519 public key": 32, "Ed25519 signature": len(edk.sign(b"m")),
             "RSA-2048 public key (DER)": len(rpk), "RSA-2048 signature": 256,
             "ML-DSA-65 public key": len(pk), "ML-DSA-65 secret key": len(sk), "ML-DSA-65 signature": len(sig)}
    write_csv("data_sizes_bytes.csv", ["item", "bytes"], [[k, v] for k, v in sizes.items()])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    def bars(a, labels, vals, cols, title, base):
        b = a.bar(labels, vals, color=cols)
        a.set_yscale("log"); a.set(title=title, ylabel="bytes (log scale)"); a.tick_params(axis="x", labelsize=8)
        for r, v in zip(b, vals):
            txt = f"{v:,} B" + ("" if v == base else f"\n{v / base:.0f}x")
            a.text(r.get_x() + r.get_width() / 2, v * 1.15, txt, ha="center", fontsize=8, color=DARK)
        a.set_ylim(10, max(vals) * 6)
    bars(ax[0], ["X25519\nkey share", "ML-KEM-768\npublic key", "ML-KEM-768\nciphertext"],
         [32, len(ek), len(ct)], [LAV, TEAL, TEAL], "Key exchange: what crosses the network", 32)
    bars(ax[1], ["Ed25519\nsignature", "RSA-2048\nsignature", "ML-DSA-65\nsignature"],
         [64, 256, len(sig)], [LAV, LAV, PUR], "Signatures: what crosses the network", 64)
    fig.suptitle("Post-quantum messages are bigger (sizes measured from our code; x = times the classical size)",
                 fontweight="bold", y=1.03)
    save(fig, "fig5_pqc_sizes.png")
    return sizes


# ---------------------------------------------------------------- fig 6: timing
def _time(fn, reps: int) -> tuple[float, float]:
    xs = []
    for _ in range(reps):
        t = time.perf_counter(); fn(); xs.append((time.perf_counter() - t) * 1000)
    return st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)


def fig_timing(reps: int) -> dict:
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    pk, sk = pqc.sig_keygen(); msg = b"isolate node 7"; sig = pqc.sign(sk, msg)
    ops = {"ML-KEM keygen": lambda: pqc.kem_keygen(), "ML-KEM encaps": lambda: pqc.kem_encaps(ek),
           "ML-KEM decaps": lambda: pqc.kem_decaps(dk, ct), "ML-DSA keygen": lambda: pqc.sig_keygen(),
           "ML-DSA sign": lambda: pqc.sign(sk, msg), "ML-DSA verify": lambda: pqc.verify(pk, msg, sig)}
    res = {k: _time(f, reps) for k, f in ops.items()}
    cx = x25519.X25519PrivateKey.generate(); peer = x25519.X25519PrivateKey.generate().public_key()
    edk = ed25519.Ed25519PrivateKey.generate(); esig = edk.sign(msg); epk = edk.public_key()
    rk = rsa.generate_private_key(65537, 2048); rsig = rk.sign(msg, __import__("cryptography").hazmat.primitives.asymmetric.padding.PKCS1v15(),
                                                            __import__("cryptography").hazmat.primitives.hashes.SHA256())
    classical = {"X25519 keygen": _time(lambda: x25519.X25519PrivateKey.generate(), reps),
                 "X25519 exchange": _time(lambda: cx.exchange(peer), reps),
                 "Ed25519 sign": _time(lambda: edk.sign(msg), reps), "Ed25519 verify": _time(lambda: epk.verify(esig, msg), reps),
                 "RSA-2048 keygen": _time(lambda: rsa.generate_private_key(65537, 2048), max(3, reps // 5))}
    write_csv("data_timing_ms.csv", ["operation", "mean_ms", "std_ms", "implementation"],
              [[k, round(v[0], 3), round(v[1], 3), "pure Python (educational)"] for k, v in res.items()] +
              [[k, round(v[0], 3), round(v[1], 3), "OpenSSL via cryptography (C)"] for k, v in classical.items()])
    fig, ax = plt.subplots(figsize=(9, 4.4))
    names = list(res); means = [res[k][0] for k in names]; sds = [res[k][1] for k in names]
    ax.bar(names, means, yerr=sds, capsize=3, color=[TEAL] * 3 + [PUR] * 3)
    for i, v in enumerate(means):
        ax.text(i, v + max(means) * 0.02, f"{v:.1f} ms", ha="center", fontsize=8)
    ax.set(ylabel="milliseconds", title=f"ML-KEM-768 and ML-DSA-65 operation time (mean of {reps} runs)")
    ax.tick_params(axis="x", labelsize=8)
    fig.text(0.5, -0.03, "Pure-Python educational code. Optimised C implementations (liboqs, OpenSSL 3.5+) are far faster, "
             "so compare sizes, not these timings, with classical crypto.", ha="center", fontsize=8, color=LAV)
    save(fig, "fig6_pqc_timing.png")
    return {k: round(v[0], 2) for k, v in {**res, **classical}.items()}


# ---------------------------------------------------------------- fig 7: pipeline
def fig_pipeline(runs: int) -> dict:
    clean = [secure_channel("192.168.1.14", seed=100 + i) for i in range(runs)]
    eve = [secure_channel("192.168.1.14", eve_fraction=1.0, seed=300 + i) for i in range(runs)]
    ok = [r for r in clean if r["status"] == "secure_channel_established"]
    phases = ["qrng_ms", "bb84_ms", "ml_kem_ms", "hkdf_aes_ms", "ml_dsa_ms"]
    means = [st.mean(r["timings_ms"][p] for r in ok) for p in phases]
    write_csv("data_pipeline_runs.csv", ["scenario", "run", "status", "qber", "total_ms"],
              [["clean", i, r["status"], r["qber"], r["key_gen_time_ms"]] for i, r in enumerate(clean)] +
              [["eavesdropper", i, r["status"], r["qber"], r["key_gen_time_ms"]] for i, r in enumerate(eve)])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1.6, 1]})
    left = 0
    for p, m, c in zip(phases, means, [PUR, ORG, TEAL, GOLD, LAV]):
        ax[0].barh(["Stage 2\n(clean run)"], [m], left=left, color=c, label=f"{p[:-3].replace('_', '-')}: {m:.1f} ms")
        left += m
    ax[0].set(xlabel="milliseconds", title=f"Where the time goes (mean of {len(ok)} successful runs, total {left:.0f} ms)")
    ax[0].legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.25)); ax[0].grid(False)
    bp = ax[1].boxplot([[r["key_gen_time_ms"] for r in clean], [r["key_gen_time_ms"] for r in eve]],
                       tick_labels=["secure channel\nestablished", "eavesdropper\n(aborted)"], patch_artist=True)
    for patch, c in zip(bp["boxes"], [TEAL, ORG]):
        patch.set_facecolor(c); patch.set_alpha(0.5)
    ax[1].set(ylabel="milliseconds", title="Total time per run")
    save(fig, "fig7_pipeline_latency.png")
    return {"runs": runs, "clean_established": len(ok), "eve_aborted": sum(r["status"] == "aborted_eavesdrop_detected" for r in eve),
            "mean_total_ms_clean": round(st.mean(r["key_gen_time_ms"] for r in ok), 1),
            "phase_mean_ms": dict(zip(phases, map(lambda v: round(v, 1), means)))}


# ---------------------------------------------------------------- attack tests + scorecard
def attack_tests() -> list[tuple[str, bool]]:
    out = []
    pk, sk = pqc.sig_keygen(); sig = pqc.sign(sk, b"isolate node 7")
    out.append(("Edited message under a valid signature", not pqc.verify(pk, b"reconnect node 7", sig)))
    out.append(("Edited signature bytes", not pqc.verify(pk, b"isolate node 7", bytes([sig[0] ^ 1]) + sig[1:])))
    out.append(("Signature checked with the wrong key", not pqc.verify(pqc.sig_keygen()[0], b"isolate node 7", sig)))
    s = CommandSigner(); v = CommandVerifier(s.public_key)
    c = s.sign("n1", "isolate"); v.verify(c)
    out.append(("Replayed command", v.verify(c)[1] == "replay_detected"))
    f = s.sign("n1", "isolate"); f["payload"]["action"] = "reconnect"
    out.append(("Forged 'reconnect' order", v.verify(f)[1] == "bad_signature"))
    out.append(("Command from an attacker's key", CommandVerifier(s.public_key).verify(CommandSigner().sign("n1", "reconnect"))[1] == "bad_signature"))
    out.append(("Stale command (old timestamp)", CommandVerifier(s.public_key).verify(s.sign("n1", "isolate", now=1.0))[1] == "stale_command"))
    out.append(("Action outside the allowlist", CommandVerifier(s.public_key).verify(s.sign("n1", "format_disk"))[1] == "action_not_allowed"))
    key = derive_session_key(b"a" * 32, b"b" * 32, b"n"); blob = encrypt(key, b"data", b"n")
    try:
        decrypt(key, blob[:-1] + bytes([blob[-1] ^ 1]), b"n"); ok = False
    except InvalidTag:
        ok = True
    out.append(("Edited encrypted traffic (AES-GCM)", ok))
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    out.append(("Edited ML-KEM ciphertext", pqc.kem_decaps(dk, bytes([ct[0] ^ 1]) + ct[1:]) != ss))
    return out


def fig_scorecard(S: dict, attacks: list[tuple[str, bool]]) -> None:
    fig = plt.figure(figsize=(12.5, 6.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 12.5); ax.set_ylim(0, 6.4)
    ax.text(0.4, 6.0, "Stage 2 results scorecard", fontsize=17, fontweight="bold", color=DARK)
    ax.text(0.4, 5.62, f"All numbers measured by experiments/run_all.py on {SUMMARY['machine']['platform']}", fontsize=8.5, color=LAV)
    q, d, p, z = S["qber"], S["detection"], S["pipeline"], S["qrng"]
    tiles = [(f"{q['clean_qber_mean']:.0%}", "QBER, clean channel", TEAL),
             (f"{q['eve_full_qber_mean']:.0%}", "QBER, full eavesdropper\n(theory: 25%)", ORG),
             (f"{q['eve_full_detect_rate']:.0%}", f"eavesdropper runs flagged\n({q['trials_per_point']} runs, {q['qubits_per_run']} qubits)", ORG),
             (f"{p['clean_established']}/{p['runs']}", "clean runs: channel\nestablished", TEAL),
             (f"{p['eve_aborted']}/{p['runs']}", "eavesdropper runs:\naborted safely", ORG),
             (f"{p['mean_total_ms_clean'] / 1000:.2f} s", "mean time to secure\nchannel (simulated)", PUR),
             ("PASS" if z["all_pass"] else "FAIL", f"QRNG randomness checks\n({z['bytes']:,} bytes)", TEAL if z["all_pass"] else ORG),
             (f"{sum(a for _, a in attacks)}/{len(attacks)}", "attack tests rejected", TEAL)]
    for i, (big, small, col) in enumerate(tiles):
        x, y = 0.4 + (i % 4) * 1.75, 3.55 - (i // 4) * 1.75
        ax.add_patch(plt.Rectangle((x, y), 1.6, 1.55, color=col, alpha=0.12, lw=0)); ax.add_patch(plt.Rectangle((x, y + 1.45), 1.6, 0.1, color=col, lw=0))
        ax.text(x + 0.8, y + 0.98, big, ha="center", va="center", fontsize=19, fontweight="bold", color=col)
        ax.text(x + 0.8, y + 0.36, small, ha="center", va="center", fontsize=7.5, color=DARK)
    ax.text(7.7, 5.0, "Attacks tried against our code", fontsize=11, fontweight="bold", color=DARK)
    for i, (name, ok) in enumerate(attacks):
        y = 4.6 - i * 0.42
        ax.text(7.7, y, "REJECTED" if ok else "ACCEPTED!", fontsize=8, fontweight="bold", color=TEAL if ok else ORG, va="center")
        ax.text(8.75, y, name, fontsize=8.5, color=DARK, va="center")
    ax.text(0.4, 0.25, "Honest limits: QRNG and BB84 are simulated in Qiskit; ML-KEM/ML-DSA run in educational pure Python (not for production).",
            fontsize=8, color=LAV)
    save(fig, "fig8_scorecard.png", tight=False)


# ---------------------------------------------------------------- RESULTS.md
def write_results_md(S: dict, attacks) -> None:
    sz = S["sizes"]
    md = f"""# Stage 2 Results

Generated by `python -m experiments.run_all` ({'quick mode' if S['quick'] else 'full mode'}). Machine: {S['machine']['platform']}, Python {S['machine']['python']}, Qiskit {S['machine']['qiskit']}.

![scorecard](fig8_scorecard.png)

## 1. Architecture
![architecture](fig0_architecture.png)

## 2. QRNG quality (simulated)
![qrng](fig1_qrng_quality.png)

Monobit p = {S['qrng']['monobit_p']}, chi-square z = {S['qrng']['chi2_z']}, serial correlation r = {S['qrng']['serial_r']}. These are basic sanity checks, not the full NIST SP 800-22 suite.
The simulator's randomness is pseudo-random; this demonstrates the circuit and workflow only.

## 3. BB84
![walkthrough](fig2_bb84_walkthrough.png)
![qber](fig3_qber_experiments.png)
![detection](fig4_detection_vs_qubits.png)

| Measurement | Value |
|---|---|
| Mean QBER, clean channel | {S['qber']['clean_qber_mean']:.4f} |
| Mean QBER, Eve intercepts every qubit | {S['qber']['eve_full_qber_mean']:.4f} (theory 0.25) |
| Eavesdropper runs flagged (full interception) | {S['qber']['eve_full_detect_rate']:.0%} |

Reading the charts: a partial eavesdropper who touches less than about 44% of the qubits stays under the 11% limit (0.25 x 0.44 = 0.11), so the threshold alone does not catch her. In our pipeline such a run still aborts, because the two keys no longer match (we do not implement error correction).

## 4. Post-quantum sizes and speed
![sizes](fig5_pqc_sizes.png)
![timing](fig6_pqc_timing.png)

Sizes are exact. Timings are from pure-Python educational code and are NOT comparable with C implementations.

| Item | Bytes |
|---|---|
""" + "\n".join(f"| {k} | {v:,} |" for k, v in sz.items()) + f"""

## 5. End-to-end pipeline
![pipeline](fig7_pipeline_latency.png)

Mean phase times (ms): {S['pipeline']['phase_mean_ms']}.

## 6. Attack tests
| Attack | Result |
|---|---|
""" + "\n".join(f"| {n} | {'rejected' if ok else 'ACCEPTED (bug)'} |" for n, ok in attacks) + "\n"
    (OUT / "RESULTS.md").write_text(md)
    print("  saved RESULTS.md")


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    q = a.quick
    OUT.mkdir(exist_ok=True)
    import qiskit
    SUMMARY.update(quick=q, machine={"platform": f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPUs",
                                     "python": platform.python_version(), "qiskit": qiskit.__version__})
    print("Stage 2 experiments", "(quick)" if q else "(full)")
    fig_architecture()
    SUMMARY["qrng"] = fig_qrng(1024 if q else 4096)
    fig_bb84_walkthrough()
    SUMMARY["qber"] = fig_qber(6 if q else 20, 512 if q else 1024)
    SUMMARY["detection"] = fig_detection(20 if q else 100)
    SUMMARY["sizes"] = fig_sizes()
    SUMMARY["timing_ms"] = fig_timing(5 if q else 20)
    SUMMARY["pipeline"] = fig_pipeline(5 if q else 20)
    attacks = attack_tests()
    SUMMARY["attacks"] = {n: ok for n, ok in attacks}
    fig_scorecard(SUMMARY, attacks)
    (OUT / "summary.json").write_text(json.dumps(SUMMARY, indent=2, default=str))
    write_results_md(SUMMARY, attacks)
    print("Done. Open results/RESULTS.md")


if __name__ == "__main__":
    main()
