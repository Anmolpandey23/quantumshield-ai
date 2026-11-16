"""Train all Stage 1 models and save them to artifacts/.

    python -m stage1.train --data synthetic                                  # 2-3 minutes on a laptop CPU
    python -m stage1.train --data cicids --data-dir D:/datasets/CIC-IDS2017  # real data (see docs)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import numpy as np
import torch
from sklearn.metrics import classification_report, f1_score

from . import data as D
from .classifier import train_classifier
from .config import ARTIFACTS_DIR, BENIGN, FEATURES
from .cpc import calibrate_cpc, make_sequences, train_cpc
from .dygnn import build_host_index, build_snapshots, evaluate_dygnn, train_dygnn
from .preprocess import Preprocessor
from .tabddpm import TabDDPM


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description="Train QuantumShield Stage 1")
    ap.add_argument("--data", choices=["synthetic", "cicids"], default="synthetic")
    ap.add_argument("--data-dir", default=None, help="folder with CIC-IDS2017 TrafficLabelling CSVs")
    ap.add_argument("--max-rows", type=int, default=400_000, help="cap on rows loaded from CIC-IDS2017")
    ap.add_argument("--out", default=str(ARTIFACTS_DIR))
    ap.add_argument("--epochs-ddpm", type=int, default=40)
    ap.add_argument("--epochs-clf", type=int, default=20)
    ap.add_argument("--epochs-cpc", type=int, default=15)
    ap.add_argument("--epochs-gnn", type=int, default=8)
    ap.add_argument("--ddpm-steps", type=int, default=200)
    ap.add_argument("--target-per-class", type=int, default=3000, help="TabDDPM lifts each rare class to this many rows")
    ap.add_argument("--seq-len", type=int, default=16)
    ap.add_argument("--snapshot-seconds", type=int, default=60)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quick", action="store_true", help="tiny settings for a smoke test")
    a = ap.parse_args(argv)
    if a.quick:
        a.epochs_ddpm, a.epochs_clf, a.epochs_cpc, a.epochs_gnn, a.ddpm_steps, a.target_per_class = 3, 4, 2, 2, 30, 400

    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    t0 = time.time()
    print(f"[1/6] loading data ({a.data}) on {a.device}")
    df = D.load(a.data, a.data_dir, max_rows=a.max_rows, seed=a.seed)
    print(f"      {len(df):,} flows, {df['Source IP'].nunique():,} source hosts\n      {df['Label'].value_counts().to_dict()}")

    # ---- flow-level split (classifier + TabDDPM)
    prep = Preprocessor().fit(df)
    X, y = prep.transform(df), prep.encode(df["Label"])
    tr, va, te = D.stratified_split(y, a.seed)
    n_cls = len(prep.classes)
    metrics: dict = {"classes": prep.classes, "n_flows": int(len(df))}

    # ---- TabDDPM: synthetic rare-attack flows (TRAIN rows only, so val/test stay untouched)
    print("[2/6] TabDDPM: learning to generate attack flows")
    ddpm = TabDDPM(len(FEATURES), n_cls, timesteps=a.ddpm_steps, device=a.device)
    ddpm.fit(X[tr][:200_000], y[tr][:200_000], epochs=a.epochs_ddpm)
    Xs, ys = ddpm.balance(X[tr], y[tr], a.target_per_class, seed=a.seed)
    print(f"      generated {len(ys):,} synthetic flows for rare classes")
    ddpm.save(str(out / "tabddpm.pt"))

    # ---- classifier, with and without synthetic data (ablation = proof TabDDPM helps)
    print("[3/6] classifier (baseline vs. with TabDDPM data)")
    base, f1_base = train_classifier(X[tr], y[tr], X[va], y[va], n_cls, a.epochs_clf, device=a.device, verbose=False, seed=a.seed)
    clf, _ = train_classifier(np.concatenate([X[tr], Xs]), np.concatenate([y[tr], ys]), X[va], y[va], n_cls,
                              a.epochs_clf, device=a.device, seed=a.seed)
    pred_te = clf.predict_proba(X[te]).argmax(1)
    f1_aug = f1_score(y[te], pred_te, average="macro", zero_division=0)
    f1_base_te = f1_score(y[te], base.predict_proba(X[te]).argmax(1), average="macro", zero_division=0)
    metrics["classifier"] = {"macro_f1_test_with_tabddpm": round(float(f1_aug), 4),
                             "macro_f1_test_baseline": round(float(f1_base_te), 4),
                             "synthetic_rows": int(len(ys)),
                             "report": classification_report(y[te], pred_te, labels=range(n_cls), target_names=prep.classes,
                                                             output_dict=True, zero_division=0)}
    print(f"      test macro-F1: baseline {f1_base_te:.4f}  ->  with TabDDPM {f1_aug:.4f}")
    torch.save({"state": clf.state_dict(), "cfg": clf.cfg}, out / "classifier.pt")

    # ---- CPC Transformer on BENIGN per-host sequences (time-block split)
    print("[4/6] CPC Transformer: learning normal behaviour")
    btr, bva, bte = D.block_split(df["Timestamp"], seed=a.seed)
    src = df["Source IP"].to_numpy()
    benign = (df["Label"] == BENIGN).to_numpy()
    seq_tr, _ = make_sequences(X[btr & benign], src[btr & benign], a.seq_len, stride=4)
    seq_va_b, _ = make_sequences(X[bva & benign], src[bva & benign], a.seq_len, stride=4)
    if len(seq_tr) < 16:
        raise SystemExit("Too few benign sequences to train CPC. Use more data or a smaller --seq-len.")
    cpc = train_cpc(seq_tr, a.epochs_cpc, device=a.device, seq_len=a.seq_len)
    calibrate_cpc(cpc, seq_tr, seq_va_b if len(seq_va_b) else seq_tr[:256])
    seq_te, owners_te = make_sequences(X[bte], src[bte], a.seq_len, stride=4)
    if len(seq_te):
        att_te, _ = make_sequences((~benign[bte]).astype(np.float32)[:, None], src[bte], a.seq_len, stride=4)
        y_seq = (att_te[:, :, 0].mean(1) > 0.5).astype(int)
        s = cpc.score(seq_te)
        from sklearn.metrics import roc_auc_score
        metrics["cpc"] = {"auroc_attack_vs_benign_sequences": float(roc_auc_score(y_seq, s)) if len(set(y_seq)) > 1 else None,
                          "mean_score_benign": float(s[y_seq == 0].mean()) if (y_seq == 0).any() else None,
                          "mean_score_attack": float(s[y_seq == 1].mean()) if (y_seq == 1).any() else None}
        print(f"      CPC {metrics['cpc']}")
    torch.save({"state": cpc.state_dict(), "cfg": cpc.cfg, "calib": cpc.calib}, out / "cpc.pt")

    # ---- DyGNN on time snapshots (time-block split, hidden state carried across snapshots)
    print("[5/6] DyGNN: scoring hosts on the changing network graph")
    hidx = build_host_index(df)
    def snaps_of(mask):
        return build_snapshots(df[mask].reset_index(drop=True), X[mask], hidx, a.snapshot_seconds)
    s_tr, s_va, s_te = snaps_of(btr), snaps_of(bva), snaps_of(bte)
    gnn = train_dygnn(s_tr, len(hidx), a.epochs_gnn, device=a.device)
    metrics["dygnn"] = {"val": evaluate_dygnn(gnn, s_va, len(hidx)) if s_va else None,
                        "test": evaluate_dygnn(gnn, s_te, len(hidx)) if s_te else None}
    print(f"      DyGNN {metrics['dygnn']}")
    torch.save({"state": gnn.state_dict(), "cfg": gnn.cfg}, out / "dygnn.pt")

    # ---- save the rest
    print("[6/6] saving artifacts")
    (out / "preprocessor.json").write_text(json.dumps(prep.to_dict()))
    cfg = {"seq_len": a.seq_len, "snapshot_seconds": a.snapshot_seconds, "buffer_minutes": 15,
           "gnn_context_snapshots": 6, "fusion": {"gnn": 0.45, "classifier": 0.35, "cpc": 0.20},
           "trained_on": a.data, "seed": a.seed}
    (out / "config.json").write_text(json.dumps(cfg, indent=2))
    metrics["train_seconds"] = round(time.time() - t0, 1)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"done in {metrics['train_seconds']}s -> {out}")
    return metrics


if __name__ == "__main__":
    main()
