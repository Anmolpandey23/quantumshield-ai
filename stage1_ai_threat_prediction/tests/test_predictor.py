import json
import pathlib

import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from stage1.config import BENIGN
from stage1.data import make_synthetic
from stage1.predictor import ThreatPredictor
from stage1.train import main as train_main

SCHEMA = json.loads((pathlib.Path(__file__).resolve().parents[2] / "contracts" / "stage1_output.schema.json").read_text())


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


def test_unknown_node_is_benign_with_a_reason(predictor):
    o = predictor.predict("203.0.113.99")
    assert o["threat_label"] == BENIGN and o["explanation"]


def test_attack_host_ranks_above_quiet_hosts(predictor):
    df = make_synthetic(seed=11, n_minutes=60, n_episodes=6)
    att = df[df["Label"] != BENIGN]
    t = att["Timestamp"].iloc[len(att) // 2] + pd.Timedelta(minutes=2)
    window = df[df["Timestamp"] <= t]
    predictor.ingest(window)
    top = max(predictor.predict_all(), key=lambda o: o["risk_score_node"])
    assert top["risk_score_node"] > 0.3
