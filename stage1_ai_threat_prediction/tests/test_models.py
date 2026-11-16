import numpy as np
import torch

from stage1.config import FEATURES
from stage1.cpc import calibrate_cpc, make_sequences, train_cpc
from stage1.data import make_synthetic
from stage1.dygnn import build_host_index, build_snapshots, evaluate_dygnn, train_dygnn
from stage1.explain import top_reasons
from stage1.preprocess import Preprocessor
from stage1.tabddpm import TabDDPM

F = len(FEATURES)


def test_tabddpm_trains_and_generates_only_what_is_needed():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(600, F)).astype("float32"); y = np.r_[np.zeros(500), np.ones(80), np.full(20, 2)].astype(int)
    x[y == 1] += 3
    m = TabDDPM(F, 3, timesteps=20, hidden=64)
    hist = m.fit(x, y, epochs=3, verbose=False)
    assert hist[-1] < hist[0]
    xs, ys = m.balance(x, y, target_per_class=120)
    assert xs.shape == (len(ys), F) and set(ys) == {1, 2} and (ys == 2).sum() == 100
    assert np.isfinite(xs).all()


def test_cpc_gives_higher_score_to_abnormal_sequences():
    df = make_synthetic(n_minutes=120, n_episodes=0, seed=5)               # benign only
    p = Preprocessor().fit(df); x = p.transform(df)
    seqs, _ = make_sequences(x, df["Source IP"].to_numpy(), 16, 4)
    model = train_cpc(seqs, epochs=3, verbose=False)
    calibrate_cpc(model, seqs, seqs)
    normal, weird = model.score(seqs[:50]), model.score(seqs[:50] + 4.0)
    assert weird.mean() > normal.mean() + 0.2 and ((0 <= normal) & (normal <= 1)).all()


def test_dygnn_snapshots_and_training():
    df = make_synthetic(n_minutes=40, n_episodes=5, seed=6)
    x = Preprocessor().fit(df).transform(df)
    idx = build_host_index(df)
    snaps = build_snapshots(df, x, idx, 60)
    assert len(snaps) >= 30 and snaps[0].x.shape[1] == F + 4
    model = train_dygnn(snaps, len(idx), epochs=2, verbose=False)
    res = evaluate_dygnn(model, snaps, len(idx))
    assert res["auroc"] is None or 0.5 <= res["auroc"] <= 1.0


def test_explanations_pick_unusual_features_only():
    attr = np.zeros(F); attr[9] = 1.0; attr[15] = 0.5; attr[0] = 0.9
    z = np.zeros(F); z[9] = 4.0; z[15] = 2.0; z[0] = 0.1                    # feature 0 is important but NOT unusual
    r = top_reasons(attr, z)
    assert r == ["unusual packet rate", "spike in SYN flag ratio"]
