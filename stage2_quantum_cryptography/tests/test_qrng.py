import math

import numpy as np

from stage2.qrng import qrng_bits, qrng_bytes


def test_length_and_binary():
    bits = qrng_bits(2500)
    assert len(bits) == 2500 and set(np.unique(bits)) <= {0, 1}
    assert len(qrng_bytes(32)) == 32


def test_monobit_balance():
    n = 8192
    ones = int(qrng_bits(n).sum())
    assert abs(ones - n / 2) < 5 * math.sqrt(n / 4)   # within 5 standard deviations


def test_unseeded_runs_differ_and_seeded_runs_repeat():
    assert qrng_bytes(32) != qrng_bytes(32)
    assert qrng_bytes(32, seed=7) == qrng_bytes(32, seed=7)
