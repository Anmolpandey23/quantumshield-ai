import json
import pathlib
import numpy as np
import pytest
from jsonschema import Draft202012Validator

from stage1.classifier import FlowClassifier, train_lightgbm
from stage1.config import (
    CLASS_NAMES,
    CLASS_TO_ID,
    LIGHTGBM_FEATURES,
    TABDDPM_FEATURES,
    TABDDPM_THRESHOLD,
)
from stage1.data import make_synthetic
from stage1.explain import format_explanation_phrases, top_reasons
from stage1.tabddpm import TabDDPM, TabDDPMPreprocessor

ROOT = pathlib.Path(__file__).resolve().parents[2]
INFERENCE_SCHEMA = json.loads((ROOT / "contracts" / "inference_schema.json").read_text())
STAGE1_SCHEMA = json.loads((ROOT / "contracts" / "stage1_output.schema.json").read_text())


def test_tabddpm_trains_and_detects_anomalies():
    rng = np.random.default_rng(42)
    n_feats = len(TABDDPM_FEATURES)
    # Benign distribution centered around 0
    x_benign = rng.normal(0.0, 0.5, size=(400, n_feats)).astype("float32")
    m = TabDDPM(n_features=n_feats, timesteps=30, hidden=64, threshold=TABDDPM_THRESHOLD, score_timesteps=6)
    history = m.fit(x_benign, epochs=3, batch_size=128, verbose=False, seed=42)
    assert history[-1] < history[0]

    # Score benign vs anomalous (shifted distribution)
    x_attack = rng.normal(4.0, 1.2, size=(50, n_feats)).astype("float32")
    scores_benign, is_anom_benign = m.predict_anomaly(x_benign[:50])
    scores_attack, is_anom_attack = m.predict_anomaly(x_attack)

    assert scores_attack.mean() > scores_benign.mean()
    assert (scores_attack >= TABDDPM_THRESHOLD).sum() > (scores_benign >= TABDDPM_THRESHOLD).sum()


def test_lightgbm_trains_and_predicts_multiclass(tmp_path):
    df = make_synthetic(n_hosts=10, n_minutes=30, n_episodes=5, seed=12)
    labels = df["Label"].to_numpy()
    y = np.array([CLASS_TO_ID.get(str(l), 0) for l in labels], dtype=np.int64)

    clf = train_lightgbm(
        x_train=df,
        y_train=y,
        best_iteration=30,
        verbose=False,
        seed=42,
    )

    probs = clf.predict_proba(df.tail(20))
    assert probs.shape == (20, len(CLASS_NAMES))
    np.testing.assert_allclose(probs.sum(axis=1), np.ones(20), atol=1e-3)

    pred_ids, pred_names = clf.predict(df.tail(20))
    assert len(pred_ids) == 20
    assert len(pred_names) == 20
    assert all(name in CLASS_NAMES for name in pred_names)

    # Save & reload test
    txt_path = tmp_path / "lightgbm_multiclass.txt"
    bun_path = tmp_path / "cicids_lightgbm_bundle.joblib"
    clf.save(txt_path, bun_path)
    assert txt_path.exists() and bun_path.exists()

    loaded = FlowClassifier.load(txt_path, bun_path)
    probs_loaded = loaded.predict_proba(df.tail(20))
    np.testing.assert_allclose(probs, probs_loaded, atol=1e-4)


def test_shap_explainability():
    df = make_synthetic(n_hosts=10, n_minutes=30, n_episodes=4, seed=7)
    y = np.array([CLASS_TO_ID.get(str(l), 0) for l in df["Label"]], dtype=np.int64)
    clf = train_lightgbm(x_train=df, y_train=y, best_iteration=25, verbose=False)

    explanations = clf.explain(df.tail(3), k=3)
    assert len(explanations) == 3
    for exp in explanations:
        assert exp["method"] == "shap.TreeExplainer"
        assert len(exp["top_contributing_features"]) <= 3
        reasons = format_explanation_phrases(exp["top_contributing_features"])
        assert isinstance(reasons, list)


def test_explanations_top_reasons_legacy():
    F = len(LIGHTGBM_FEATURES)
    attr = np.zeros(F)
    attr[0] = 0.9  # Destination Port
    attr[12] = 1.0 # Flow Bytes/s
    z = np.zeros(F)
    z[0] = 0.1     # not unusual
    z[12] = 3.5    # unusual
    r = top_reasons(attr, z, k=2)
    assert "unusual byte rate" in r
