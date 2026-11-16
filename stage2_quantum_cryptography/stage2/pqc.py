"""Post-quantum crypto: ML-KEM-768 (FIPS 203) and ML-DSA-65 (FIPS 204).

Backend: the pure-Python libraries `kyber-py` and `dilithium-py`.
They follow the NIST standards and are great for learning and for a course
project, but they are NOT constant-time and NOT for production use.
Production path: liboqs, or OpenSSL 3.5+ which ships ML-KEM and ML-DSA.
"""
from __future__ import annotations

import hashlib

from dilithium_py.ml_dsa import ML_DSA_65
from kyber_py.ml_kem import ML_KEM_768

KEM_NAME, SIG_NAME = "ML-KEM-768", "ML-DSA-65"


def seed_from_qrng(qrng_seed: bytes) -> None:
    """Seed both libraries' deterministic random bit generators with QRNG output.

    This is the link between the quantum part and the post-quantum part:
    the keys below are derived from QRNG bytes, not from the OS random source.
    """
    ML_KEM_768.set_drbg_seed(hashlib.sha384(b"stage2-mlkem" + qrng_seed).digest())
    ML_DSA_65.set_drbg_seed(hashlib.sha384(b"stage2-mldsa" + qrng_seed).digest())


def kem_keygen() -> tuple[bytes, bytes]:
    return ML_KEM_768.keygen()          # (encapsulation key, decapsulation key)


def kem_encaps(ek: bytes) -> tuple[bytes, bytes]:
    shared, ct = ML_KEM_768.encaps(ek)  # library returns (key, ciphertext)
    return shared, ct


def kem_decaps(dk: bytes, ct: bytes) -> bytes:
    return ML_KEM_768.decaps(dk, ct)


def sig_keygen() -> tuple[bytes, bytes]:
    return ML_DSA_65.keygen()           # (public key, secret key)


def sign(sk: bytes, message: bytes) -> bytes:
    return ML_DSA_65.sign(sk, message)


def verify(pk: bytes, message: bytes, signature: bytes) -> bool:
    try:
        return bool(ML_DSA_65.verify(pk, message, signature))
    except Exception:
        return False
