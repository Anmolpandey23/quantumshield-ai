"""Hybrid session key + AES-256-GCM traffic encryption."""
from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def derive_session_key(kem_secret: bytes, qkd_key: bytes, context: bytes) -> bytes:
    """Mix the ML-KEM secret and the BB84 key into one 256-bit key with HKDF.

    Hybrid design: the session key stays safe if EITHER source stays safe.
    """
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"QuantumShield-Stage2|" + context).derive(kem_secret + qkd_key)


def encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def decrypt(key: bytes, blob: bytes, aad: bytes = b"") -> bytes:
    """Raises cryptography.exceptions.InvalidTag if the data was changed."""
    return AESGCM(key).decrypt(blob[:12], blob[12:], aad)
