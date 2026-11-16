from stage2.bb84 import bb84


def test_clean_channel_has_zero_qber_and_matching_keys():
    r = bb84(2048, seed=1)
    assert r.qber == 0.0 and not r.eavesdrop_detected and r.reason == "ok"
    assert r.keys_match and r.key_alice == r.key_bob and len(r.key_alice) == 32


def test_full_eavesdropper_is_detected():
    r = bb84(2048, eve_fraction=1.0, seed=2)
    assert 0.15 < r.qber < 0.35 and r.eavesdrop_detected
    assert r.key_alice is None and r.key_bob is None


def test_partial_eavesdropper_qber_scales():
    r = bb84(4096, eve_fraction=0.4, seed=3)
    assert 0.04 < r.qber < 0.16          # theory: 0.25 * 0.4 = 0.10


def test_honest_noise_below_threshold_is_not_flagged():
    r = bb84(4096, channel_error=0.05, seed=4)
    assert not r.eavesdrop_detected and 0.02 < r.qber < 0.09


def test_high_noise_aborts():
    assert bb84(2048, channel_error=0.2, seed=5).eavesdrop_detected


def test_too_few_qubits_gives_insufficient_material():
    assert bb84(64, seed=6).reason == "insufficient_key_material"
