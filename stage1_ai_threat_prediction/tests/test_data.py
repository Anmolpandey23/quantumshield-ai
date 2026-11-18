import numpy as np

from stage1.config import BENIGN, FEATURES
from stage1.data import block_split, make_synthetic, normalise_label, stratified_split
from stage1.preprocess import Preprocessor


def test_synthetic_has_real_columns_and_rare_attacks():
    df = make_synthetic(n_minutes=60, n_episodes=6, seed=1)
    for c in FEATURES + ["Source IP", "Destination IP", "Timestamp", "Label"]:
        assert c in df.columns
    assert (df["Label"] == BENIGN).mean() > 0.7            # attacks are rare, like real life
    assert df["Label"].nunique() >= 3


def test_label_normalisation_matches_cicids_names():
    assert normalise_label("DoS Hulk") == "DoS" and normalise_label("DoS slowloris") == "DoS"
    assert normalise_label("FTP-Patator") == "Brute Force" and normalise_label("SSH-Patator") == "Brute Force"
    assert normalise_label("Web Attack \x96 XSS") == "Web Attacks" and normalise_label(" BENIGN ") == BENIGN
    assert normalise_label("DDoS") == "DDoS" and normalise_label("PortScan") == "Port Scanning"


def test_preprocessor_roundtrip_and_benign_is_class_zero():
    df = make_synthetic(n_minutes=30, n_episodes=4, seed=2)
    p = Preprocessor().fit(df)
    assert p.classes[0] == BENIGN
    x = p.transform(df)
    assert x.shape == (len(df), len(FEATURES)) and abs(x.mean()) < 0.5 and np.isfinite(x).all()
    p2 = Preprocessor.from_dict(p.to_dict())
    assert np.allclose(p2.transform(df), x)


def test_splits_do_not_overlap_and_cover_everything():
    df = make_synthetic(n_minutes=60, n_episodes=6, seed=3)
    y = Preprocessor().fit(df).encode(df["Label"])
    for tr, va, te in (stratified_split(y), block_split(df["Timestamp"])):
        assert (tr.astype(int) + va + te == 1).all()
        assert tr.sum() > va.sum() and te.sum() > 0
