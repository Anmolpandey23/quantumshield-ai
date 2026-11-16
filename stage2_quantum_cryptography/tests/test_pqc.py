from stage2 import pqc


def test_kem_roundtrip_and_sizes():
    ek, dk = pqc.kem_keygen()
    ss, ct = pqc.kem_encaps(ek)
    assert pqc.kem_decaps(dk, ct) == ss
    assert (len(ek), len(ct), len(ss)) == (1184, 1088, 32)      # FIPS 203, ML-KEM-768


def test_tampered_ciphertext_gives_different_secret():
    ek, dk = pqc.kem_keygen()
    ss, ct = pqc.kem_encaps(ek)
    bad = bytes([ct[0] ^ 1]) + ct[1:]
    assert pqc.kem_decaps(dk, bad) != ss                         # implicit rejection


def test_signature_valid_and_sizes():
    pk, sk = pqc.sig_keygen()
    sig = pqc.sign(sk, b"isolate node 7")
    assert pqc.verify(pk, b"isolate node 7", sig)
    assert (len(pk), len(sig)) == (1952, 3309)                   # FIPS 204, ML-DSA-65


def test_tampering_is_rejected():
    pk, sk = pqc.sig_keygen()
    sig = pqc.sign(sk, b"isolate node 7")
    assert not pqc.verify(pk, b"reconnect node 7", sig)          # edited message
    assert not pqc.verify(pk, b"isolate node 7", bytes([sig[0] ^ 1]) + sig[1:])  # edited signature
    other_pk, _ = pqc.sig_keygen()
    assert not pqc.verify(other_pk, b"isolate node 7", sig)      # wrong key


def test_qrng_seed_makes_keys_reproducible():
    pqc.seed_from_qrng(b"\x01" * 32)
    a = pqc.kem_keygen()
    pqc.seed_from_qrng(b"\x01" * 32)
    assert pqc.kem_keygen() == a
    pqc.seed_from_qrng(b"\x02" * 32)
    assert pqc.kem_keygen() != a
