import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stage3_self_healing"))
sys.path.insert(0, str(ROOT / "stage2_quantum_cryptography"))
