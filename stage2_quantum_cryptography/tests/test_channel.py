import pytest
from cryptography.exceptions import InvalidTag

from stage2.channel import decrypt, derive_session_key, encrypt


def test_roundtrip_and_tamper_detection():
    key = derive_session_key(b"a" * 32, b"b" * 32, b"node-1")
    blob = encrypt(key, b"hello", b"node-1")
    assert decrypt(key, blob, b"node-1") == b"hello"
    with pytest.raises(InvalidTag):
        decrypt(key, blob[:-1] + bytes([blob[-1] ^ 1]), b"node-1")   # edited data
    with pytest.raises(InvalidTag):
        decrypt(key, blob, b"node-2")                                # wrong context


def test_hybrid_key_depends_on_both_inputs():
    k = derive_session_key(b"a" * 32, b"b" * 32, b"n")
    assert k != derive_session_key(b"x" * 32, b"b" * 32, b"n")
    assert k != derive_session_key(b"a" * 32, b"x" * 32, b"n")
