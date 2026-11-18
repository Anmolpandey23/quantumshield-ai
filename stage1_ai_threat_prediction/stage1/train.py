"""Train QuantumShield Stage 1 Models: TabDDPM Anomaly Detector + LightGBM Attack Classifier.

Usage:
    python -m stage1.train --data synthetic
    python -m stage1.train --data cicids --data-dir <path_to_csvs>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score
import torch

from . import data as D
from .classifier import FlowClassifier, train_lightgbm
from .config import (
    ARTIFACTS_DIR,
    CLASS_NAMES,
    CLASS_TO_ID,
    LIGHTGBM_FEATURES,
    MODELS_DIR,
    PROJECT_ROOT,
    ROOT,
    TABDDPM_FEATURES,
    TABDDPM_SCORE_SEED,
    TABDDPM_SCORE_TIMESTEPS,
    TABDDPM_STEPS,
    TABDDPM_THRESHOLD,
)
from .preprocess import Preprocessor
from .tabddpm import TabDDPM, TabDDPMPreprocessor


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description="Train QuantumShield TabDDPM and LightGBM models")
    ap.add_argument("--data", choices=["synthetic", "cicids"], default="synthetic")
    ap.add_argument("--data-dir", default=None, help="folder with CIC-IDS2017 TrafficLabelling CSVs")
    ap.add_argument("--max-rows", type=int, default=200_000, help="cap on rows loaded from CIC-IDS2017")
    ap.add_argument("--out", default=str(ARTIFACTS_DIR))
    ap.add_argument("--epochs-ddpm", type=int, default=10)
    ap.add_argument("--lgb-rounds", type=int, default=100)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true", help="smoke test settings")
    a = ap.parse_args(argv)

    if a.quick:
        a.epochs_ddpm = 2
        a.lgb_rounds = 20

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    target_models_dir = PROJECT_ROOT / "models" if PROJECT_ROOT.exists() else ROOT / "models"
    tabddpm_dir = target_models_dir / "tabddpm" / "improved"
    lgb_dir = target_models_dir / "cicids_classifier"
    tabddpm_dir.mkdir(parents=True, exist_ok=True)
    lgb_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"[1/4] Loading {a.data} dataset...")
    df = D.load(a.data, a.data_dir, max_rows=a.max_rows, seed=a.seed)
    print(f"      {len(df):,} flows, {df['Label'].value_counts().to_dict()}")

    # 1. Preprocessing and Splits
    prep = Preprocessor().fit(df)
    labels = df["Label"].to_numpy()
    y = np.array([CLASS_TO_ID.get(str(l), 0) for l in labels], dtype=np.int64)
    tr, va, te = D.stratified_split(y, a.seed)

    metrics: dict = {
        "classes": list(CLASS_NAMES),
        "n_flows": int(len(df)),
    }

    # 2. Train TabDDPM on benign ("Normal Traffic") flows only
    print(f"[2/4] Training TabDDPM benign-distribution anomaly detector on {a.device}...")
    benign_mask = (y == CLASS_TO_ID["Normal Traffic"])
    df_benign_train = df[tr & benign_mask]
    tabddpm_prep = TabDDPMPreprocessor().fit(df_benign_train)
    X_tab_benign = tabddpm_prep.transform(df_benign_train)

    tabddpm = TabDDPM(
        n_features=len(TABDDPM_FEATURES),
        timesteps=TABDDPM_STEPS,
        threshold=TABDDPM_THRESHOLD,
        score_timesteps=TABDDPM_SCORE_TIMESTEPS,
        device=a.device,
    )
    tabddpm.fit(X_tab_benign, epochs=a.epochs_ddpm, batch_size=256, verbose=True, seed=a.seed)

    # Save TabDDPM artifacts
    tabddpm_pt_path = tabddpm_dir / "tabddpm_improved.pt"
    tabddpm_prep_path = tabddpm_dir / "preprocessing_improved.joblib"
    tabddpm.save(tabddpm_pt_path)
    tabddpm_prep.save(tabddpm_prep_path)
    # Also save copy in out
    tabddpm.save(out / "tabddpm_improved.pt")
    tabddpm.save(out / "tabddpm.pt")
    tabddpm_prep.save(out / "preprocessing_improved.joblib")
    print(f"      Saved TabDDPM to {tabddpm_pt_path}")

    # Evaluate TabDDPM on test set
    X_tab_test = tabddpm_prep.transform(df[te])
    scores_te, is_anom_te = tabddpm.predict_anomaly(X_tab_test)
    y_test_anom = (y[te] != CLASS_TO_ID["Normal Traffic"]).astype(int)
    from sklearn.metrics import roc_auc_score
    try:
        auroc = float(roc_auc_score(y_test_anom, scores_te)) if len(set(y_test_anom)) > 1 else 1.0
    except Exception:
        auroc = 1.0
    metrics["tabddpm"] = {
        "auroc": round(auroc, 4),
        "mean_score_benign": round(float(scores_te[y_test_anom == 0].mean()), 4) if (y_test_anom == 0).any() else 0.0,
        "mean_score_anomaly": round(float(scores_te[y_test_anom == 1].mean()), 4) if (y_test_anom == 1).any() else 0.0,
        "threshold": TABDDPM_THRESHOLD,
    }
    print(f"      TabDDPM Test AUROC: {auroc:.4f}")

    # 3. Train LightGBM Multiclass Attack Classifier on 52 features
    print(f"[3/4] Training LightGBM multiclass flow classifier ({len(LIGHTGBM_FEATURES)} features)...")
    clf = train_lightgbm(
        x_train=df[tr],
        y_train=y[tr],
        x_val=df[va],
        y_val=y[va],
        feature_columns=LIGHTGBM_FEATURES,
        class_names=CLASS_NAMES,
        best_iteration=a.lgb_rounds,
        seed=a.seed,
        verbose=True,
    )

    # Save LightGBM artifacts
    lgb_txt_path = lgb_dir / "lightgbm_multiclass.txt"
    lgb_bundle_path = lgb_dir / "cicids_lightgbm_bundle.joblib"
    clf.save(lgb_txt_path, lgb_bundle_path)
    # Also save copy in out
    clf.save(out / "lightgbm_multiclass.txt", out / "cicids_lightgbm_bundle.joblib")
    print(f"      Saved LightGBM to {lgb_txt_path} and {lgb_bundle_path}")

    # Evaluate LightGBM on test set
    preds_te = clf.predict_proba(df[te]).argmax(axis=1)
    f1 = f1_score(y[te], preds_te, average="macro", zero_division=0)
    report = classification_report(y[te], preds_te, labels=range(len(CLASS_NAMES)), target_names=CLASS_NAMES, output_dict=True, zero_division=0)
    metrics["lightgbm"] = {
        "macro_f1": round(float(f1), 4),
        "report": report,
    }
    print(f"      LightGBM Test macro-F1: {f1:.4f}")

    # 4. Save metadata & configs
    print("[4/4] Saving manifests and configurations...")
    cfg = {
        "seq_len": 16,
        "buffer_minutes": 15,
        "threshold_ddpm": TABDDPM_THRESHOLD,
        "classes": CLASS_NAMES,
        "n_features": len(LIGHTGBM_FEATURES),
        "trained_on": a.data,
        "seed": a.seed,
    }
    (out / "config.json").write_text(json.dumps(cfg, indent=2))
    (out / "preprocessor.json").write_text(json.dumps(prep.to_dict(), indent=2))
    metrics["train_seconds"] = round(time.time() - t0, 1)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Save SHAP metadata reference if needed
    shap_meta_dir = PROJECT_ROOT / "results" / "cicids_classifier" / "shap"
    shap_meta_dir.mkdir(parents=True, exist_ok=True)
    (shap_meta_dir / "shap_experiment_metadata.json").write_text(json.dumps({
        "method": "shap.TreeExplainer",
        "model_output": "raw",
        "sample_size": min(len(df[te]), 700),
    }, indent=2))

    print(f"Stage 1 training complete in {metrics['train_seconds']}s -> {out}")
    return metrics


if __name__ == "__main__":
    main()
