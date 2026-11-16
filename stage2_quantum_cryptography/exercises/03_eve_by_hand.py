"""Exercise 3: predict the QBER before you see it.
Eve intercepts every qubit. Work out on paper why the answer is about 25%, then run:
    python exercises/03_eve_by_hand.py
Hint: Eve guesses the basis wrong half the time. When she does, Bob's answer is a coin flip.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stage2.bb84 import bb84  # noqa: E402

for frac in (0.0, 0.5, 1.0):
    r = bb84(2048, eve_fraction=frac, seed=42)
    print(f"Eve intercepts {frac:>4.0%} of qubits -> QBER {r.qber:.1%}, aborted: {r.eavesdrop_detected}")
