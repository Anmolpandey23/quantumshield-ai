import json
import pathlib

import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from stage1.config import BENIGN, CLASS_NAMES
from stage1.data import make_synthetic
from stage1.predictor import ThreatPredictor
from stage1.train import main as train_main

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts" / "stage1_output.schema.json").read_text())
INFERENCE_CONTRACT = json.loads((ROOT / "contracts" / "inference_schema.json").read_text())


@pytest.fixture(scope="module")
def predictor(tmp_path_factory):
    out = tmp_path_factory.mktemp("artifacts")
    train_main(["--data", "synthetic", "--quick", "--out", str(out)])
    return ThreatPredictor.load(out)


def test_output_satisfies_the_stage1_contract(predictor):
    df = make_synthetic(seed=9, n_minutes=40, n_episodes=5)
    predictor.ingest(df)
    outs = predictor.predict_all()
    assert outs
    v = Draft202012Validator(SCHEMA)
    for o in outs:
        assert not list(v.iter_errors(o)), o


def test_output_satisfies_tabddpm_lightgbm_inference_contract(predictor):
    df = make_synthetic(seed=9, n_minutes=40, n_episodes=5)
    predictor.ingest(df)
    outs = predictor.predict_all()
    assert outs

    required_fields = INFERENCE_CONTRACT["fields"]
    for o in outs:
        assert "event_id" in o and isinstance(o["event_id"], str)
        assert "timestamp_utc" in o and isinstance(o["timestamp_utc"], str)

        # TabDDPM validation
        assert "tabddpm" in o
        assert isinstance(o["tabddpm"]["anomaly_score"], (int, float))
        assert isinstance(o["tabddpm"]["threshold"], (int, float))
        assert isinstance(o["tabddpm"]["is_anomaly"], bool)

        # LightGBM validation
        assert "lightgbm" in o
        assert isinstance(o["lightgbm"]["predicted_class"], str)
        assert isinstance(o["lightgbm"]["predicted_class_id"], int)
        assert isinstance(o["lightgbm"]["class_probabilities"], dict)
        assert set(o["lightgbm"]["class_probabilities"].keys()) == set(CLASS_NAMES)

        # Explainability validation
        assert "explainability" in o
        assert o["explainability"]["method"] == "shap.TreeExplainer"
        assert isinstance(o["explainability"]["top_contributing_features"], list)

        # Risk and Response validation
        assert "risk_assessment" in o
        assert "risk_level" in o["risk_assessment"]
        assert "response" in o
        assert "execution_status" in o["response"]
        assert o["response"]["execution_status"] in ("pending_approval", "simulated", "executed")


def test_unknown_node_is_benign_with_a_reason(predictor):
    o = predictor.predict("203.0.113.99")
    assert o["threat_label"] == BENIGN and o["explanation"]
    assert o["lightgbm"]["predicted_class"] == "Normal Traffic"
    assert o["tabddpm"]["is_anomaly"] is False


def test_attack_host_ranks_above_quiet_hosts(predictor):
    df = make_synthetic(seed=11, n_minutes=60, n_episodes=6)
    att = df[df["Label"] != "Normal Traffic"]
    t = att["Timestamp"].iloc[len(att) // 2] + pd.Timedelta(minutes=2)
    window = df[df["Timestamp"] <= t]
    predictor.ingest(window)
    top = max(predictor.predict_all(), key=lambda o: o["risk_score_node"])
    assert top["risk_score_node"] > 0.3
    assert top["threat_label"] != "Normal Traffic" or top["tabddpm"]["is_anomaly"]
