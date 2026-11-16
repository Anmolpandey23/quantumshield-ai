from stage2.pipeline import secure_channel

REQUIRED = {"node_id", "key_generation_method", "shared_key_id", "kem_ciphertext",
            "signature_public_key", "eavesdrop_detected", "qber", "key_gen_time_ms", "status"}


def test_clean_run_establishes_channel():
    r = secure_channel("10.0.0.5", {"confidence": 0.9}, seed=11)
    assert r["status"] == "secure_channel_established" and REQUIRED <= set(r)
    assert r["qber"] == 0.0 and r["sizes_bytes"]["kem_ciphertext"] == 1088


def test_eavesdropper_aborts_before_any_key_is_used():
    r = secure_channel("10.0.0.5", eve_fraction=1.0, seed=12)
    assert r["status"] == "aborted_eavesdrop_detected" and r["eavesdrop_detected"]
    assert "kem_ciphertext" not in r


def test_two_runs_give_different_keys():
    a, b = secure_channel("n", seed=1), secure_channel("n", seed=2)
    assert a["shared_key_id"] != b["shared_key_id"]
