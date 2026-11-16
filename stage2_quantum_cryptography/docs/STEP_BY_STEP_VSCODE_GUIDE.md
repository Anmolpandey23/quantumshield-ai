# Stage 2 Step-by-Step Guide (VS Code): Learn and Build Together
## Quantum-Safe Cryptography: QRNG, BB84, ML-KEM, ML-DSA

This guide takes you from an empty folder to a finished, tested, visualised and GitHub-ready Stage 2. You will create every file yourself in VS Code. After each file you run one command and compare with the **Expected output** shown here. Every command and every output in this guide was run on a clean install before being written down.

**How each step works:** LEARN (2 minutes) → CREATE the file → RUN → CHECK the output → ANSWER the self-test.

**Time:** about 2 to 3 days if you work 3 to 4 hours a day.

**What you will have at the end**
- A working Python package `stage2/` with QRNG, BB84, ML-KEM, ML-DSA, hybrid AES-GCM encryption and signed commands.
- 25 automated tests, all passing.
- 9 result figures, CSV data files and an auto-written `results/RESULTS.md`.
- A private GitHub repo with CI.

**Honest limits (say these yourself before anyone asks)**
- QRNG and BB84 are **simulated** in Qiskit. The simulator's randomness is pseudo-random, so this shows the circuits and workflow, not real quantum randomness.
- ML-KEM-768 and ML-DSA-65 are the real NIST standards, but we use pure-Python educational libraries (`kyber-py`, `dilithium-py`). They are not constant-time and not for production. The production path is liboqs or OpenSSL 3.5+.
- Our BB84 has no error-correction step. If keys differ, the pipeline aborts.

---

# PART 1: Install the tools (once)

## 1.1 Python 3.12 (3.11 also works)
1. Download from python.org and install.
2. **Windows:** on the first installer screen tick **"Add python.exe to PATH"**. This one checkbox causes most "python is not recognized" errors.
3. Check (open a new terminal first):
```bash
python3 --version      # Mac / Linux
python --version       # Windows
```
Expected: `Python 3.12.x` or `3.11.x`. Do not use 3.13 or newer for this project; the pinned packages were tested on 3.11 and 3.12.

## 1.2 Git
Download from git-scm.com and install with default options. Check:
```bash
git --version
git config --global user.name "Your Name"
git config --global user.email "the-email-on-your-github-account"
git config --global init.defaultBranch main
```

## 1.3 VS Code and extensions
1. Install VS Code from code.visualstudio.com.
2. Open it, click the Extensions icon (left bar, or `Ctrl+Shift+X`), and install: **Python** (Microsoft), **Pylance** (Microsoft). Optional: **GitLens**.

## 1.4 GitHub account
Create one at github.com and turn on two-factor authentication.

**VS Code shortcuts you will use**
| Action | Keys |
|---|---|
| Open terminal | Ctrl + backtick key (the key left of 1) |
| Command palette | `Ctrl+Shift+P` |
| Save file | `Ctrl+S` |
| Preview a Markdown file | `Ctrl+Shift+V` |
| Source Control panel | `Ctrl+Shift+G` |
| View an image | click the `.png` in the Explorer |

---

# PART 2: Create the project and the environment

## 2.1 Create the folder and open it
Create a folder named `quantumshield-stage2` (for example inside Documents). In VS Code: **File → Open Folder** and choose it. Everything below happens inside this folder.

## 2.2 Open the terminal
Ctrl + backtick key (or **Terminal → New Terminal**). Check it is in your project folder:
```bash
pwd            # Mac / Linux / Git Bash
cd             # Windows Command Prompt
Get-Location   # Windows PowerShell
```

## 2.3 Create the virtual environment
A virtual environment is a private box of Python packages for this project only.
```bash
python3 -m venv venv           # Mac / Linux
python -m venv venv            # Windows (or:  py -3.12 -m venv venv)
```

## 2.4 Activate it (do this in every new terminal)
```bash
source venv/bin/activate              # Mac / Linux
.\venv\Scripts\Activate.ps1           # Windows PowerShell
venv\Scripts\activate.bat             # Windows Command Prompt
source venv/Scripts/activate          # Windows Git Bash
```
**Check:** your prompt now starts with `(venv)`.

**Windows PowerShell says "running scripts is disabled"?** Run this once, then activate again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 2.5 Tell VS Code to use it
`Ctrl+Shift+P`, type **Python: Select Interpreter**, choose the one that shows `./venv`. Check: the bottom-right corner of VS Code shows the venv Python.

## 2.6 Create `requirements.txt` and install
Create the file (Explorer → New File icon → `requirements.txt`), paste this, save:
```text
# Tested with Python 3.12 (3.11 also works). Exact versions = same behaviour on every teammate's laptop.
qiskit==2.6.1
qiskit-aer==0.18.0
cryptography==46.0.6
numpy==2.4.4
matplotlib==3.10.8
kyber-py==1.2.0
dilithium-py==1.5.1
pycryptodome==4.2.0
pytest==9.1.1
```
Install (2 to 4 minutes):
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2.7 Verify the install
```bash
python -c "import qiskit, qiskit_aer, kyber_py, dilithium_py, cryptography, matplotlib; print('all imports OK')"
```
Expected: `all imports OK`. If you see `No module named ...`, your venv is not active (go back to 2.4).

---

# PART 3: Create the folder structure and config files

**Mac / Linux / Git Bash:**
```bash
mkdir -p stage2 experiments tests exercises results docs scripts
touch stage2/__init__.py experiments/__init__.py
```
**Windows PowerShell:**
```powershell
mkdir stage2, experiments, tests, exercises, results, docs, scripts
New-Item stage2/__init__.py, experiments/__init__.py -ItemType File
```
The two `__init__.py` files stay **empty**. They tell Python these folders are packages.

Create `pytest.ini` in the project root:
```ini
[pytest]
pythonpath = .
testpaths = tests
```
Create `.gitignore` in the project root:
```text
# Python
__pycache__/
*.py[cod]
.pytest_cache/
venv/
.venv/
*.egg-info/
# Secrets and local files
.env
*.pem
*.key
.vscode/
.idea/
.DS_Store
# Keep results/ (figures + CSV) in Git on purpose; ignore only big temp files
results/run_log.txt
```

Your tree now looks like:
```text
quantumshield-stage2/
├── venv/              (not uploaded to Git)
├── stage2/            (the package)
├── experiments/
├── tests/
├── exercises/
├── results/
├── docs/
├── scripts/
├── pytest.ini
├── requirements.txt
└── .gitignore
```

---

# PART 4: Build Stage 2 step by step

For each file: Explorer → right-click the folder → **New File** → type the path name → paste the code → `Ctrl+S`. Always run commands **from the project root**, with `(venv)` showing.

## STEP 1: One qubit (warm-up)
**LEARN:** a normal bit is 0 or 1. A qubit can be in a mix of both (superposition) until you measure it. The **Hadamard (H) gate** creates an equal mix. Measuring gives 0 or 1 at random, 50/50.

**PREDICT:** out of 1000 measurements, how many 0s and 1s?

**CREATE** `exercises/01_hello_qubit.py`:
```python
"""Exercise 1: one qubit, one Hadamard gate, many measurements.
Predict first: how many 0s and 1s out of 1000?   Run:  python exercises/01_hello_qubit.py
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

qc = QuantumCircuit(1, 1)
qc.h(0)             # superposition of 0 and 1
qc.measure(0, 0)    # collapse to a plain bit
print(qc.draw())
print("counts:", AerSimulator().run(qc, shots=1000).result().get_counts())
```
**RUN:**
```bash
python exercises/01_hello_qubit.py
```
**Expected output** (counts differ a little every run):
```text
     ┌───┐┌─┐
  q: ┤ H ├┤M├
     └───┘└╥┘
c: 1/══════╩═
           0 
counts: {'1': 486, '0': 514}
```
**SELF-TEST:** What does `qc.h(0)` do? Why are the counts not exactly 500/500? *(Answer: it puts qubit 0 in superposition. Measurement is random, so counts wobble around 500.)*

## STEP 2: Bases (the heart of BB84)
**LEARN:** a qubit can be prepared and read in two "bases": `+` (the Z basis) and `x` (the X basis, reached with an H gate). Read in the **right** basis and you get a certain answer. Read in the **wrong** basis and you get a coin flip. BB84 and eavesdrop detection both rest on this.

**PREDICT** each of the four lines before running.

**CREATE** `exercises/02_basis_intuition.py`:
```python
"""Exercise 2: why a wrong basis gives a random answer. This is the heart of BB84.
Predict each result before you run.   Run:  python exercises/02_basis_intuition.py
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

sim = AerSimulator()


def run(label, build):
    qc = QuantumCircuit(1, 1)
    build(qc)
    qc.measure(0, 0)
    print(f"{label:55} -> {sim.run(qc, shots=1000).result().get_counts()}")


run("A: prepare |0>, measure in the + basis (right basis)", lambda qc: None)
run("B: prepare |+> (H), measure in the + basis (WRONG basis)", lambda qc: qc.h(0))
run("C: prepare |+> (H), then H again, measure (right basis)", lambda qc: (qc.h(0), qc.h(0)))
run("D: prepare |1> (X), measure in the + basis", lambda qc: qc.x(0))
```
**RUN:**
```bash
python exercises/02_basis_intuition.py
```
**Expected output:**
```text
A: prepare |0>, measure in the + basis (right basis)    -> {'0': 1000}
B: prepare |+> (H), measure in the + basis (WRONG basis) -> {'0': 532, '1': 468}
C: prepare |+> (H), then H again, measure (right basis) -> {'0': 1000}
D: prepare |1> (X), measure in the + basis              -> {'1': 1000}
```
**SELF-TEST:** Why is line B random but line C certain? *(Answer: B reads a `|+>` state in the wrong basis. In C, a second H undoes the first, so the qubit is back to `|0>`.)*

## STEP 3: QRNG, the quantum random number generator
**LEARN:** a QRNG applies H to many qubits and measures them. Each result is a random bit. Eight bits make a byte. We batch up to 1024 qubits per circuit because one circuit per bit is very slow. We use Qiskit's **stabilizer** simulator, which is fast for circuits made only of H, X and measure.

**Honest note:** a simulator's randomness is pseudo-random. Real randomness needs real quantum hardware.

**CREATE** `stage2/qrng.py`:
```python
"""QRNG: a quantum random number generator, simulated with Qiskit.

Idea: put each qubit in superposition with a Hadamard (H) gate, then measure it.
The outcome is 0 or 1 with 50/50 probability.

HONEST NOTE: on a simulator the "randomness" comes from the simulator's own
pseudo-random sampler. This code demonstrates the QRNG *circuit and workflow*.
True quantum randomness needs real quantum hardware or a physical QRNG device.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

CHUNK = 1024  # qubits per circuit (stabilizer simulator memory grows with n^2)
_SIM = AerSimulator(method="stabilizer")  # H, X, measure are all Clifford gates


def measure_bits(qc: QuantumCircuit, seed: int | None = None) -> np.ndarray:
    """Run a circuit once and return the measured classical bits as a 0/1 array.

    Qiskit prints the highest classical bit first, so we reverse the string
    to make index i of the array equal to classical bit i.
    """
    opts = {} if seed is None else {"seed_simulator": int(seed)}
    memory = _SIM.run(qc, shots=1, memory=True, **opts).result().get_memory()[0]
    return np.fromiter((int(c) for c in reversed(memory.replace(" ", ""))), dtype=np.uint8)


def qrng_bits(n_bits: int, seed: int | None = None) -> np.ndarray:
    """Return n_bits random bits (uint8 array of 0/1). Batches qubits per circuit."""
    chunks, remaining, i = [], n_bits, 0
    while remaining > 0:
        k = min(CHUNK, remaining)
        qc = QuantumCircuit(k, k)
        qc.h(range(k))                      # superposition
        qc.measure(range(k), range(k))      # collapse to 0 or 1
        chunks.append(measure_bits(qc, None if seed is None else seed + i))
        remaining -= k
        i += 1
    return np.concatenate(chunks)


def qrng_bytes(n_bytes: int, seed: int | None = None) -> bytes:
    """Return n_bytes random bytes."""
    return np.packbits(qrng_bits(8 * n_bytes, seed)).tobytes()
```
**RUN:**
```bash
python -c "from stage2.qrng import qrng_bytes; print(qrng_bytes(32).hex())"
```
**Expected:** 64 hex characters, different every time. Example:
```text
5c37f4c625f6a1ee4de531a34054f796c0a32c6048c3eb6d313a77b59ac089fe
```
**SELF-TEST:** Why 64 hex characters for 32 bytes? Why is `seed` optional? *(Answer: each byte is 2 hex digits. A seed makes runs repeatable for tests and plots.)*

## STEP 4: BB84 quantum key distribution
**LEARN:**
1. Alice sends random bits, each encoded in a random basis.
2. Bob measures each qubit in a random basis.
3. They announce **only their bases** and keep positions where the bases matched (about half). This is **sifting**.
4. They reveal a sample of those bits and count mismatches. That fraction is the **QBER**.
5. Clean channel: QBER near 0. An eavesdropper who measures and resends gets the basis wrong half the time, and then Bob is wrong half of those times: 0.5 x 0.5 = **25%** error. We **abort above 11%**.

**CREATE** `stage2/bb84.py`:
```python
"""BB84 quantum key distribution, simulated with Qiskit (stabilizer simulator).

Roles: Alice sends qubits, Bob measures them, Eve optionally intercepts.
Eve uses the classic intercept-resend attack: she measures in a random basis
and resends what she saw. This disturbs ~25% of the sifted bits she touches.

Both circuits are batched (one qubit per transmitted bit), so a run needs only
two simulator calls. Everything quantum is really simulated, including Eve's
measurements.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit

from .qrng import measure_bits

THRESHOLD = 0.11   # abort if estimated QBER is above ~11% (BB84 security limit)
MIN_RAW_KEY = 128  # minimum raw key bits needed after sifting and testing


@dataclass
class BB84Result:
    n_qubits: int
    sifted_len: int
    test_len: int
    raw_key_len: int
    qber: float
    threshold: float
    eavesdrop_detected: bool
    reason: str                 # "ok" | "qber_above_threshold" | "insufficient_key_material"
    keys_match: bool
    key_alice: bytes | None
    key_bob: bytes | None
    eve_fraction: float
    channel_error: float
    details: dict = field(default_factory=dict, repr=False)

    def summary(self) -> dict:
        return {
            "n_qubits": self.n_qubits, "sifted_len": self.sifted_len,
            "test_len": self.test_len, "raw_key_len": self.raw_key_len,
            "qber": round(self.qber, 4), "threshold": self.threshold,
            "eavesdrop_detected": self.eavesdrop_detected, "reason": self.reason,
            "keys_match": self.keys_match,
            "eve_fraction": self.eve_fraction, "channel_error": self.channel_error,
        }


def _prepare(qc: QuantumCircuit, q: int, bit: int, basis: int) -> None:
    """Encode `bit` in `basis` (0 = Z basis '+', 1 = X basis 'x')."""
    if bit:
        qc.x(q)
    if basis:
        qc.h(q)


def privacy_amplify(bits: np.ndarray) -> bytes:
    """Compress the raw key into a 256-bit key with SHA-256 (simple privacy amplification)."""
    return hashlib.sha256(np.packbits(bits).tobytes()).digest()


def bb84(n_qubits: int = 2048, eve_fraction: float = 0.0, channel_error: float = 0.0,
         threshold: float = THRESHOLD, test_fraction: float = 0.25,
         seed: int | None = None) -> BB84Result:
    """Run one BB84 session.

    eve_fraction  : share of qubits Eve intercepts (0 = no eavesdropper, 1 = all)
    channel_error : probability that Bob's detector flips a bit (honest noise)
    test_fraction : share of sifted bits revealed to estimate QBER
    """
    rng = np.random.default_rng(seed)
    n = n_qubits
    alice_bits = rng.integers(0, 2, n)
    alice_bases = rng.integers(0, 2, n)
    bob_bases = rng.integers(0, 2, n)
    intercepted = rng.random(n) < eve_fraction
    eve_bases = rng.integers(0, 2, n)

    def sim_seed() -> int:
        return int(rng.integers(0, 2**31 - 1))

    # Circuit 1: Alice prepares; Eve measures the qubits she intercepts.
    eve_bits = np.zeros(n, dtype=np.uint8)
    if intercepted.any():
        qc1 = QuantumCircuit(n, n)
        for q in range(n):
            _prepare(qc1, q, int(alice_bits[q]), int(alice_bases[q]))
            if intercepted[q]:
                if eve_bases[q]:
                    qc1.h(q)
                qc1.measure(q, q)
        eve_bits = measure_bits(qc1, sim_seed())

    # Circuit 2: qubits travel to Bob (Eve re-prepares what she measured), Bob measures.
    qc2 = QuantumCircuit(n, n)
    for q in range(n):
        if intercepted[q]:
            _prepare(qc2, q, int(eve_bits[q]), int(eve_bases[q]))
        else:
            _prepare(qc2, q, int(alice_bits[q]), int(alice_bases[q]))
        if bob_bases[q]:
            qc2.h(q)
        qc2.measure(q, q)
    bob_bits = measure_bits(qc2, sim_seed())
    if channel_error > 0:
        bob_bits = bob_bits ^ (rng.random(n) < channel_error).astype(np.uint8)

    # Sifting: keep positions where Alice's and Bob's bases matched.
    matched = np.flatnonzero(alice_bases == bob_bases)
    perm = rng.permutation(matched)
    n_test = max(1, int(round(len(matched) * test_fraction))) if len(matched) else 0
    test_idx, key_idx = perm[:n_test], np.sort(perm[n_test:])

    qber = float(np.mean(alice_bits[test_idx] != bob_bits[test_idx])) if n_test else 1.0
    if qber > threshold:
        reason = "qber_above_threshold"
    elif len(key_idx) < MIN_RAW_KEY:
        reason = "insufficient_key_material"
    else:
        reason = "ok"
    abort = reason != "ok"

    ka, kb = alice_bits[key_idx].astype(np.uint8), bob_bits[key_idx].astype(np.uint8)
    keys_match = bool(np.array_equal(ka, kb)) and not abort
    return BB84Result(
        n_qubits=n, sifted_len=len(matched), test_len=n_test, raw_key_len=len(key_idx),
        qber=qber, threshold=threshold, eavesdrop_detected=(reason == "qber_above_threshold"),
        reason=reason, keys_match=keys_match,
        key_alice=None if abort else privacy_amplify(ka),
        key_bob=None if abort else privacy_amplify(kb),
        eve_fraction=eve_fraction, channel_error=channel_error,
        details={"alice_bits": alice_bits, "alice_bases": alice_bases, "bob_bases": bob_bases,
                 "bob_bits": bob_bits, "intercepted": intercepted, "test_idx": test_idx,
                 "key_idx": key_idx},
    )
```
**RUN:**
```bash
python -c "from stage2.bb84 import bb84; print(bb84(2048, seed=3).summary()); print(bb84(2048, eve_fraction=1, seed=3).summary())"
```
**Expected** (line 1 clean, line 2 with an eavesdropper):
```text
{'n_qubits': 2048, 'sifted_len': 1018, 'test_len': 254, 'raw_key_len': 764, 'qber': 0.0, 'threshold': 0.11, 'eavesdrop_detected': False, 'reason': 'ok', 'keys_match': True, 'eve_fraction': 0.0, 'channel_error': 0.0}
{'n_qubits': 2048, 'sifted_len': 1018, 'test_len': 254, 'raw_key_len': 764, 'qber': 0.2165, 'threshold': 0.11, 'eavesdrop_detected': True, 'reason': 'qber_above_threshold', 'keys_match': False, 'eve_fraction': 1, 'channel_error': 0.0}
```
**CHECK:** line 1 has `qber: 0.0` and `eavesdrop_detected: False`. Line 2 has `qber` around 0.2 to 0.3 and `eavesdrop_detected: True`.

**Now the prediction exercise.** Create `exercises/03_eve_by_hand.py`:
```python
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
```
```bash
python exercises/03_eve_by_hand.py
```
**Expected:**
```text
Eve intercepts   0% of qubits -> QBER 0.0%, aborted: False
Eve intercepts  50% of qubits -> QBER 14.7%, aborted: True
Eve intercepts 100% of qubits -> QBER 27.4%, aborted: True
```
**SELF-TEST:** Why is the QBER at 50% interception only about 12.5% in theory? *(Answer: Eve touches half the qubits, so 0.25 x 0.5. A partial eavesdropper under about 44% stays below the 11% limit, which is why a short test can miss her.)*

## STEP 5: Encrypting traffic with AES-256-GCM and a hybrid key
**LEARN:** public-key methods agree on a key; a fast symmetric cipher (AES) then encrypts the data. **AES-GCM** also detects tampering. We mix the ML-KEM secret and the BB84 key with **HKDF** into one 256-bit key. This is a *hybrid*: the session key stays safe if either source stays safe.

**CREATE** `stage2/channel.py`:
```python
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
```
**RUN:**
```bash
python -c "from stage2.channel import *; k=derive_session_key(b'a'*32,b'b'*32,b'n'); b=encrypt(k,b'hello'); print(decrypt(k,b))"
```
**Expected:**
```text
b'hello'
```

## STEP 6: Post-quantum crypto: ML-KEM and ML-DSA
**LEARN:**
- **ML-KEM (FIPS 203, formerly Kyber):** the receiver makes a public key and a secret key. The sender uses the public key to make a **ciphertext** and a **shared secret**. The receiver recovers the same secret from the ciphertext. Both then hold the same 32-byte secret.
- **ML-DSA (FIPS 204, formerly Dilithium):** the signer signs with a secret key; anyone verifies with the public key. Change one byte and verification fails.
- Both rest on **lattice** problems that no known quantum algorithm solves quickly.
- `seed_from_qrng()` below is the **link between the quantum and post-quantum halves**: the key generators are seeded with QRNG bytes.

**CREATE** `stage2/pqc.py`:
```python
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
```
**RUN (ML-KEM):**
```bash
python -c "from stage2 import pqc; ek,dk=pqc.kem_keygen(); ss,ct=pqc.kem_encaps(ek); print(len(ek),len(ct),len(ss),pqc.kem_decaps(dk,ct)==ss)"
```
**Expected** (public key, ciphertext, secret sizes in bytes, then `True`):
```text
1184 1088 32 True
```
**RUN (ML-DSA):**
```bash
python -c "from stage2 import pqc; pk,sk=pqc.sig_keygen(); s=pqc.sign(sk,b'hi'); print(len(pk),len(s),pqc.verify(pk,b'hi',s),pqc.verify(pk,b'ho',s))"
```
**Expected** (public key size, signature size, genuine message `True`, edited message `False`):
```text
1952 3309 True False
```
**SELF-TEST:** Why are these much bigger than X25519 (32 B) and Ed25519 (64 B)? What could that do to a Stage 1 detector trained on classical traffic? *(Answer: lattice keys and signatures are larger, so handshakes look different and may be misread as attacks.)*

## STEP 7: Signed commands for Stage 3
**LEARN:** Stage 3's RL agent will send `isolate`, `monitor` or `reconnect`. If an attacker could forge `reconnect`, the whole system is useless. So every command is **signed**, and the verifier rejects: a bad signature, an action not on the allowlist (a guardrail), an old timestamp, and a replayed nonce.

**CREATE** `stage2/commands.py`:
```python
"""Signed commands for Stage 3 (isolate / monitor / reconnect).

Every command is signed with ML-DSA. The verifier rejects:
  - forged or edited commands   (bad signature)
  - actions outside the allowlist (guardrail)
  - old commands                (stale timestamp)
  - re-sent commands            (replay: nonce already seen)
"""
from __future__ import annotations

import json
import os
import time

from . import pqc

ALLOWED_ACTIONS = {"isolate", "monitor", "reconnect"}


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class CommandSigner:
    def __init__(self) -> None:
        self.public_key, self._secret_key = pqc.sig_keygen()

    def sign(self, node_id: str, action: str, now: float | None = None) -> dict:
        payload = {"node_id": node_id, "action": action,
                   "issued_at": time.time() if now is None else now,
                   "nonce": os.urandom(16).hex()}
        return {"payload": payload, "signature": pqc.sign(self._secret_key, _canonical(payload)).hex()}


class CommandVerifier:
    def __init__(self, public_key: bytes, max_age_s: float = 30.0) -> None:
        self.public_key = public_key
        self.max_age_s = max_age_s
        self._seen: set[str] = set()

    def verify(self, signed: dict, now: float | None = None) -> tuple[bool, str]:
        now = time.time() if now is None else now
        try:
            payload, sig = signed["payload"], bytes.fromhex(signed["signature"])
        except (KeyError, ValueError, TypeError):
            return False, "malformed_command"
        if not pqc.verify(self.public_key, _canonical(payload), sig):
            return False, "bad_signature"
        if payload.get("action") not in ALLOWED_ACTIONS:
            return False, "action_not_allowed"
        if abs(now - payload.get("issued_at", 0)) > self.max_age_s:
            return False, "stale_command"
        if payload.get("nonce") in self._seen:
            return False, "replay_detected"
        self._seen.add(payload["nonce"])
        return True, "ok"
```

## STEP 8: The full pipeline and the demo
**LEARN:** the pipeline is the Stage 2 function Stage 1 triggers and Stage 3 consumes: QRNG → BB84 (abort if QBER > 11%) → ML-KEM → hybrid key and AES-GCM check → ML-DSA signed event. It returns a dictionary with status, QBER, timings and sizes.

**CREATE** `stage2/pipeline.py`:
```python
"""Stage 2 pipeline: QRNG -> BB84 -> ML-KEM -> hybrid key + AES-GCM -> ML-DSA."""
from __future__ import annotations

import json
import time

from . import pqc
from .bb84 import bb84
from .channel import decrypt, derive_session_key, encrypt
from .qrng import qrng_bytes


def secure_channel(node_id: str, stage1_output: dict | None = None, *, n_qubits: int = 2048,
                   eve_fraction: float = 0.0, channel_error: float = 0.0,
                   seed: int | None = None) -> dict:
    """Establish a quantum-safe channel for `node_id`. Returns the Stage 2 output contract."""
    timings: dict[str, float] = {}
    t_start = time.perf_counter()

    def lap(name: str, t0: float) -> float:
        timings[name] = round((time.perf_counter() - t0) * 1000, 2)
        return time.perf_counter()

    t = time.perf_counter()
    qrng_seed = qrng_bytes(32, seed)                       # 1. quantum random seed
    pqc.seed_from_qrng(qrng_seed)                          #    seeds the PQC key generators
    t = lap("qrng_ms", t)

    bb = bb84(n_qubits=n_qubits, eve_fraction=eve_fraction, channel_error=channel_error,
              seed=None if seed is None else seed + 1)     # 2. BB84 key agreement
    t = lap("bb84_ms", t)
    if bb.reason != "ok" or not bb.keys_match:
        status = ("aborted_eavesdrop_detected" if bb.eavesdrop_detected
                  else "aborted_insufficient_key_material" if bb.reason == "insufficient_key_material"
                  else "aborted_key_mismatch")
        return {"node_id": node_id, "status": status, "eavesdrop_detected": bb.eavesdrop_detected,
                "qber": round(bb.qber, 4), "reason": bb.reason,
                "key_gen_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
                "timings_ms": timings}

    ek, dk = pqc.kem_keygen()                              # 3. ML-KEM key establishment
    ss_sender, ct = pqc.kem_encaps(ek)
    ss_receiver = pqc.kem_decaps(dk, ct)
    t = lap("ml_kem_ms", t)

    ctx = node_id.encode()                                 # 4. hybrid session key + AES-256-GCM
    key_sender = derive_session_key(ss_sender, bb.key_alice, ctx)
    key_receiver = derive_session_key(ss_receiver, bb.key_bob, ctx)
    probe = b"stage2 traffic check"
    traffic_ok = decrypt(key_receiver, encrypt(key_sender, probe, ctx), ctx) == probe
    t = lap("hkdf_aes_ms", t)

    sig_pk, sig_sk = pqc.sig_keygen()                      # 5. ML-DSA signed event
    event = json.dumps({"node_id": node_id, "event": "channel_established",
                        "qber": round(bb.qber, 4)}, sort_keys=True).encode()
    signature = pqc.sign(sig_sk, event)
    sig_ok = pqc.verify(sig_pk, event, signature)
    t = lap("ml_dsa_ms", t)

    ok = traffic_ok and sig_ok and ss_sender == ss_receiver and key_sender == key_receiver
    return {
        "node_id": node_id,
        "key_generation_method": "QRNG+BB84+ML-KEM-768 (hybrid HKDF)",
        "shared_key_id": f"key_{node_id}_{key_sender.hex()[:8]}",
        "kem_ciphertext": ct.hex(),
        "signature_public_key": sig_pk.hex(),
        "signature": signature.hex(),
        "eavesdrop_detected": False,
        "qber": round(bb.qber, 4),
        "key_gen_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        "timings_ms": timings,
        "sizes_bytes": {"kem_public_key": len(ek), "kem_ciphertext": len(ct),
                        "sig_public_key": len(sig_pk), "signature": len(signature)},
        "status": "secure_channel_established" if ok else "failed_self_check",
    }
```
**CREATE** `stage2/demo.py`:
```python
"""Command-line demo:  python -m stage2.demo"""
from .commands import CommandSigner, CommandVerifier
from .pipeline import secure_channel


def show(title: str, r: dict) -> None:
    print(f"\n=== {title} ===")
    for k in ("node_id", "status", "qber", "eavesdrop_detected", "key_generation_method",
              "key_gen_time_ms", "timings_ms", "sizes_bytes"):
        if k in r:
            print(f"  {k:24}: {r[k]}")


if __name__ == "__main__":
    show("Clean channel", secure_channel("192.168.1.14", seed=1))
    show("Eavesdropper on the line", secure_channel("192.168.1.14", eve_fraction=1.0, seed=2))
    print("\n=== Signed commands (for Stage 3) ===")
    signer = CommandSigner()
    verifier = CommandVerifier(signer.public_key)
    cmd = signer.sign("192.168.1.14", "isolate")
    print("  genuine command   :", verifier.verify(cmd))
    print("  replayed command  :", verifier.verify(cmd))
    forged = signer.sign("192.168.1.14", "isolate")
    forged["payload"]["action"] = "reconnect"
    print("  forged (edited)   :", verifier.verify(forged))
```
**RUN:**
```bash
python -m stage2.demo
```
**Expected** (timings differ on your machine):
```text

=== Clean channel ===
  node_id                 : 192.168.1.14
  status                  : secure_channel_established
  qber                    : 0.0
  eavesdrop_detected      : False
  key_generation_method   : QRNG+BB84+ML-KEM-768 (hybrid HKDF)
  key_gen_time_ms         : 710.14
  timings_ms              : {'qrng_ms': 39.8, 'bb84_ms': 623.51, 'ml_kem_ms': 11.44, 'hkdf_aes_ms': 1.26, 'ml_dsa_ms': 34.06}
  sizes_bytes             : {'kem_public_key': 1184, 'kem_ciphertext': 1088, 'sig_public_key': 1952, 'signature': 3309}

=== Eavesdropper on the line ===
  node_id                 : 192.168.1.14
  status                  : aborted_eavesdrop_detected
  qber                    : 0.2165
  eavesdrop_detected      : True
  key_gen_time_ms         : 1237.84
  timings_ms              : {'qrng_ms': 7.0, 'bb84_ms': 1230.82}

=== Signed commands (for Stage 3) ===
  genuine command   : (True, 'ok')
  replayed command  : (False, 'replay_detected')
  forged (edited)   : (False, 'bad_signature')
```
**CHECK:** the clean run says `secure_channel_established` with QBER 0.0. The eavesdropper run says `aborted_eavesdrop_detected` and **no key is used**. The three command checks show `(True, 'ok')`, `(False, 'replay_detected')`, `(False, 'bad_signature')`.

## STEP 9: Automated tests
**LEARN:** a test is a small program that checks one claim. If all tests pass, you know the core promises still hold after any change.

**CREATE** these six files, one by one:

`tests/test_qrng.py`
```python
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
```
`tests/test_bb84.py`
```python
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
```
`tests/test_channel.py`
```python
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
```
`tests/test_pqc.py`
```python
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
```
`tests/test_commands.py`
```python
from stage2.commands import CommandSigner, CommandVerifier


def make():
    s = CommandSigner()
    return s, CommandVerifier(s.public_key, max_age_s=30)


def test_genuine_command_is_accepted():
    s, v = make()
    assert v.verify(s.sign("n1", "isolate")) == (True, "ok")


def test_forged_edit_is_rejected():
    s, v = make()
    cmd = s.sign("n1", "isolate")
    cmd["payload"]["action"] = "reconnect"
    assert v.verify(cmd) == (False, "bad_signature")


def test_replay_is_rejected():
    s, v = make()
    cmd = s.sign("n1", "monitor")
    assert v.verify(cmd)[0] is True
    assert v.verify(cmd) == (False, "replay_detected")


def test_stale_command_is_rejected():
    s, v = make()
    assert v.verify(s.sign("n1", "isolate", now=1000.0), now=2000.0) == (False, "stale_command")


def test_action_outside_allowlist_is_rejected():
    s, v = make()
    assert v.verify(s.sign("n1", "format_disk")) == (False, "action_not_allowed")


def test_attacker_key_and_garbage_are_rejected():
    s, v = make()
    assert v.verify(CommandSigner().sign("n1", "reconnect")) == (False, "bad_signature")
    assert v.verify({"nope": 1}) == (False, "malformed_command")
```
`tests/test_pipeline.py`
```python
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
```
**RUN:**
```bash
python -m pytest -v
```
**Expected** (the last line says `25 passed`):
```text
rootdir: /home/claude/qs2
configfile: pytest.ini
testpaths: tests
collecting ... collected 25 items

tests/test_bb84.py::test_clean_channel_has_zero_qber_and_matching_keys PASSED [  4%]
tests/test_bb84.py::test_full_eavesdropper_is_detected PASSED            [  8%]
tests/test_bb84.py::test_partial_eavesdropper_qber_scales PASSED         [ 12%]
tests/test_bb84.py::test_honest_noise_below_threshold_is_not_flagged PASSED [ 16%]
tests/test_bb84.py::test_high_noise_aborts PASSED                        [ 20%]
tests/test_bb84.py::test_too_few_qubits_gives_insufficient_material PASSED [ 24%]
tests/test_channel.py::test_roundtrip_and_tamper_detection PASSED        [ 28%]
tests/test_channel.py::test_hybrid_key_depends_on_both_inputs PASSED     [ 32%]
tests/test_commands.py::test_genuine_command_is_accepted PASSED          [ 36%]
tests/test_commands.py::test_forged_edit_is_rejected PASSED              [ 40%]
tests/test_commands.py::test_replay_is_rejected PASSED                   [ 44%]
tests/test_commands.py::test_stale_command_is_rejected PASSED            [ 48%]
tests/test_commands.py::test_action_outside_allowlist_is_rejected PASSED [ 52%]
tests/test_commands.py::test_attacker_key_and_garbage_are_rejected PASSED [ 56%]
tests/test_pipeline.py::test_clean_run_establishes_channel PASSED        [ 60%]
tests/test_pipeline.py::test_eavesdropper_aborts_before_any_key_is_used PASSED [ 64%]
tests/test_pipeline.py::test_two_runs_give_different_keys PASSED         [ 68%]
tests/test_pqc.py::test_kem_roundtrip_and_sizes PASSED                   [ 72%]
tests/test_pqc.py::test_tampered_ciphertext_gives_different_secret PASSED [ 76%]
tests/test_pqc.py::test_signature_valid_and_sizes PASSED                 [ 80%]
tests/test_pqc.py::test_tampering_is_rejected PASSED                     [ 84%]
tests/test_pqc.py::test_qrng_seed_makes_keys_reproducible PASSED         [ 88%]
tests/test_qrng.py::test_length_and_binary PASSED                        [ 92%]
tests/test_qrng.py::test_monobit_balance PASSED                          [ 96%]
tests/test_qrng.py::test_unseeded_runs_differ_and_seeded_runs_repeat PASSED [100%]

============================= 25 passed ==============================
```
**If a test fails:** read the line starting with `E`. It shows the value that was wrong. A BB84 test can fail very rarely by chance because BB84 is random; run again, and if it fails twice there is a real bug.

## STEP 10: Experiments and visualisations
**LEARN:** the experiment script runs many trials and turns the numbers into pictures you can put in a report. It also writes CSV files and a `RESULTS.md` page.

**CREATE** `experiments/run_all.py` (paste the whole file):
```python
"""Run every Stage 2 experiment and write figures, CSV files and RESULTS.md.

    python -m experiments.run_all           # full run (about 5 minutes)
    python -m experiments.run_all --quick   # fewer trials (about 1 minute)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import statistics as st
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, x25519

from stage2 import pqc
from stage2.bb84 import THRESHOLD, bb84
from stage2.channel import decrypt, derive_session_key, encrypt
from stage2.commands import CommandSigner, CommandVerifier
from stage2.pipeline import secure_channel
from stage2.qrng import qrng_bits

PUR, TEAL, ORG, GOLD, DARK, LAV = "#7E48D6", "#0F8A64", "#D9622B", "#B8860B", "#1B0F2E", "#5B4B7A"
OUT = Path("results")
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 150, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.labelsize": 10, "font.size": 9})
SUMMARY: dict = {}


def save(fig, name: str, tight: bool = True) -> None:
    if tight:
        fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved", name)


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ---------------------------------------------------------------- fig 0: architecture
def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 4.2))
    ax.axis("off"); ax.set_xlim(0, 12.5); ax.set_ylim(0, 4.2)
    boxes = [("Stage 1\ninput", "node, threat,\nconfidence", LAV), ("QRNG", "Hadamard +\nmeasure", PUR),
             ("BB84", "sift, test QBER,\nabort > 11%", ORG), ("ML-KEM-768", "encapsulate /\ndecapsulate", TEAL),
             ("HKDF +\nAES-256-GCM", "hybrid session key,\nencrypt traffic", GOLD),
             ("ML-DSA-65", "sign events\nand commands", PUR), ("Stage 3\noutput", "key id, QBER,\nstatus, timings", LAV)]
    w, gap = 1.5, 0.33
    for i, (title, sub, col) in enumerate(boxes):
        x = 0.2 + i * (w + gap)
        ax.add_patch(plt.Rectangle((x, 1.5), w, 1.7, color=col, alpha=0.12, lw=0))
        ax.add_patch(plt.Rectangle((x, 3.0), w, 0.2, color=col, lw=0))
        ax.text(x + w / 2, 2.62, title, ha="center", va="center", fontweight="bold", fontsize=10, color=DARK)
        ax.text(x + w / 2, 1.95, sub, ha="center", va="center", fontsize=8, color=LAV)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(x + w + gap - 0.04, 2.35), xytext=(x + w + 0.04, 2.35),
                        arrowprops=dict(arrowstyle="-|>", color=DARK, lw=1.4))
    ax.annotate("", xy=(0.2 + 3 * (w + gap) + w / 2, 1.45), xytext=(0.2 + 1 * (w + gap) + w / 2, 1.45),
                arrowprops=dict(arrowstyle="-|>", color=PUR, lw=1.4, connectionstyle="arc3,rad=0.35"))
    ax.text(0.2 + 2 * (w + gap) + w / 2, 0.55, "QRNG bytes seed the ML-KEM and ML-DSA key generators",
            ha="center", fontsize=9, color=PUR, fontweight="bold")
    ax.text(6.25, 4.0, "Stage 2: Quantum-Safe Cryptography pipeline", ha="center", fontsize=13,
            fontweight="bold", color=DARK)
    ax.text(0.2 + 2 * (w + gap) + w / 2, 0.15, "Eavesdropper found: stop, no key is used", ha="center",
            fontsize=8.5, color=ORG)
    save(fig, "fig0_architecture.png")


# ---------------------------------------------------------------- fig 1: QRNG quality
def fig_qrng(n_bytes: int) -> dict:
    bits = qrng_bits(8 * n_bytes)
    data = np.packbits(bits)
    n = len(bits)
    s = 2 * int(bits.sum()) - n
    p_mono = math.erfc(abs(s) / math.sqrt(2 * n))
    counts = np.bincount(data, minlength=256)
    chi2 = float(((counts - n_bytes / 256) ** 2 / (n_bytes / 256)).sum())
    z_chi = (chi2 - 255) / math.sqrt(2 * 255)
    x = 2.0 * bits - 1
    r1 = float(np.mean(x[:-1] * x[1:]))
    tests = [("Monobit (bit balance)", f"p = {p_mono:.3f}", p_mono > 0.01),
             ("Byte chi-square (255 df)", f"z = {z_chi:+.2f}", abs(z_chi) < 3),
             ("Serial correlation (lag 1)", f"r = {r1:+.4f}", abs(r1) < 4 / math.sqrt(n))]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].bar(range(256), counts, color=PUR, width=1.0)
    ax[0, 0].axhline(n_bytes / 256, color=ORG, ls="--", label="expected if uniform")
    ax[0, 0].set(title=f"Byte values from {n_bytes:,} QRNG bytes", xlabel="byte value", ylabel="count")
    ax[0, 0].legend(frameon=False)
    ax[0, 1].imshow(bits[:64 * 128].reshape(64, 128), cmap="Purples", interpolation="nearest", aspect="auto")
    ax[0, 1].set(title="First 8,192 random bits (dark = 1)"); ax[0, 1].grid(False); ax[0, 1].set_xticks([]); ax[0, 1].set_yticks([])
    run = np.cumsum(bits) / np.arange(1, n + 1)
    ax[1, 0].plot(np.arange(1, n + 1), run, color=TEAL, lw=1)
    ax[1, 0].axhline(0.5, color=ORG, ls="--")
    ax[1, 0].set(title="Running share of ones converges to 0.5", xlabel="bits generated", ylabel="share of ones",
                 xscale="log", ylim=(0.3, 0.7))
    ax[1, 1].axis("off")
    for i, (name, val, ok) in enumerate(tests):
        y = 0.82 - i * 0.24
        ax[1, 1].add_patch(plt.Rectangle((0.02, y - 0.09), 0.96, 0.18, color=TEAL if ok else ORG, alpha=0.14, lw=0))
        ax[1, 1].text(0.05, y, name, fontweight="bold", va="center", color=DARK)
        ax[1, 1].text(0.62, y, val, va="center", color=LAV)
        ax[1, 1].text(0.93, y, "PASS" if ok else "FAIL", va="center", ha="right", fontweight="bold", color=TEAL if ok else ORG)
    ax[1, 1].set(title="Basic randomness checks", xlim=(0, 1), ylim=(0, 1))
    fig.suptitle("QRNG output quality (simulated; real randomness needs real hardware)", fontweight="bold", y=1.0)
    save(fig, "fig1_qrng_quality.png")
    return {"bytes": n_bytes, "monobit_p": round(p_mono, 4), "chi2_z": round(z_chi, 3),
            "serial_r": round(r1, 5), "all_pass": all(t[2] for t in tests)}


# ---------------------------------------------------------------- fig 2: BB84 walkthrough
def _table(ax, rows, cells, colors, title):
    ncol = len(cells[0])
    ax.set_xlim(-2.6, ncol); ax.set_ylim(-len(rows), 0.4); ax.axis("off"); ax.set_title(title, loc="left")
    for r, label in enumerate(rows):
        ax.text(-2.5, -r - 0.5, label, va="center", fontsize=8, fontweight="bold", color=DARK)
        for c in range(ncol):
            ax.add_patch(plt.Rectangle((c, -r - 1), 0.96, 0.9, color=colors[r][c], alpha=0.85, lw=0))
            ax.text(c + 0.48, -r - 0.5, cells[r][c], ha="center", va="center", fontsize=8, color=DARK)


def fig_bb84_walkthrough() -> None:
    n = 16
    pick = {}
    for eve in (0.0, 1.0):
        for seed in range(500):
            r = bb84(n, eve_fraction=eve, seed=seed, test_fraction=0.34)
            d = r.details
            m = d["alice_bases"] == d["bob_bases"]
            errs = int((d["alice_bits"][m] != d["bob_bits"][m]).sum())
            if r.test_len >= 2 and ((eve == 0.0) or (errs >= 2 and errs <= 3)):
                pick[eve] = r; break
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.2))
    for ax, eve in zip(axes, (0.0, 1.0)):
        r = pick[eve]; d = r.details
        basis = lambda b: "x" if b else "+"
        match = d["alice_bases"] == d["bob_bases"]
        rows = ["Alice bit", "Alice basis", "Bob basis", "Bob result", "Bases match?", "Role"]
        cells, cols = [[] for _ in rows], [[] for _ in rows]
        for q in range(n):
            role, rc = ("discarded", "#DDDDDD")
            if match[q]:
                if q in set(d["test_idx"]):
                    bad = d["alice_bits"][q] != d["bob_bits"][q]
                    role, rc = ("test: ERROR", ORG) if bad else ("test: ok", GOLD)
                else:
                    role, rc = "key bit", TEAL
            vals = [(int(d["alice_bits"][q]), "#E6DCF7"), (basis(d["alice_bases"][q]), "#E6DCF7"),
                    (basis(d["bob_bases"][q]), "#F3EFFA"), (int(d["bob_bits"][q]), "#F3EFFA"),
                    ("yes" if match[q] else "no", "#E6F4EE" if match[q] else "#EEEEEE"), (role.replace("test: ", "t:"), rc)]
            for i, (v, c) in enumerate(vals):
                cells[i].append(str(v)); cols[i].append(c)
        t = ("Clean channel" if eve == 0 else "Eavesdropper intercepts every qubit")
        _table(ax, rows, cells, cols, f"{t}: QBER measured on the test bits = {r.qber:.0%}"
                                         + ("   (no errors)" if eve == 0 else "   (Eve disturbed some matching-basis bits)"))
    fig.suptitle("BB84 step by step on 16 qubits (key bit = used for the key, t: = revealed to estimate QBER)",
                 fontweight="bold")
    save(fig, "fig2_bb84_walkthrough.png")


# ---------------------------------------------------------------- fig 3: QBER sweeps
def fig_qber(trials: int, n: int) -> dict:
    fr = np.round(np.linspace(0, 1, 11), 2)
    eve_rows, eve_stats = [], []
    for f in fr:
        res = [bb84(n, eve_fraction=float(f), seed=1000 + i) for i in range(trials)]
        q = [r.qber for r in res]
        eve_stats.append((f, np.mean(q), np.std(q), np.mean([r.eavesdrop_detected for r in res])))
        eve_rows += [[f, i, round(x, 4)] for i, x in enumerate(q)]
    write_csv("data_qber_vs_eve.csv", ["eve_fraction", "trial", "qber"], eve_rows)
    ps = np.round(np.linspace(0, 0.2, 11), 3)
    noise_stats = []
    for p in ps:
        q = [bb84(n, channel_error=float(p), seed=5000 + i).qber for i in range(trials)]
        noise_stats.append((p, np.mean(q), np.std(q)))
    write_csv("data_qber_vs_noise.csv", ["channel_error", "mean_qber", "std_qber"],
              [[round(a, 3), round(b, 4), round(c, 4)] for a, b, c in noise_stats])
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    f, m, s, d = zip(*eve_stats)
    ax[0].errorbar(f, m, yerr=s, fmt="o-", color=PUR, capsize=3, label="measured (simulated)")
    ax[0].plot(fr, 0.25 * fr, "--", color=GOLD, label="theory: 25% x fraction")
    ax[0].axhline(THRESHOLD, color=ORG, ls=":", label="abort threshold 11%")
    ax[0].set(title="QBER grows with eavesdropping", xlabel="fraction of qubits Eve intercepts", ylabel="QBER")
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].bar([str(int(x * 100)) + "%" for x in f], d, color=[TEAL if v < 0.5 else ORG for v in d])
    ax[1].set(title="Share of runs flagged by the 11% rule", xlabel="fraction of qubits Eve intercepts",
              ylabel="runs aborted", ylim=(0, 1.05))
    ax[1].tick_params(axis="x", labelsize=7)
    p, m2, s2 = zip(*noise_stats)
    ax[2].errorbar(p, m2, yerr=s2, fmt="o-", color=TEAL, capsize=3, label="measured")
    ax[2].plot(ps, ps, "--", color=GOLD, label="theory: QBER = noise")
    ax[2].axhline(THRESHOLD, color=ORG, ls=":", label="abort threshold 11%")
    ax[2].set(title="Honest noise also raises QBER", xlabel="detector error probability", ylabel="QBER")
    ax[2].legend(frameon=False, fontsize=8)
    fig.suptitle(f"BB84 error-rate experiments ({trials} runs per point, {n} qubits per run)", fontweight="bold", y=1.03)
    save(fig, "fig3_qber_experiments.png")
    full = [x for x in eve_stats if x[0] == 1.0][0]
    return {"clean_qber_mean": round(float(eve_stats[0][1]), 4), "eve_full_qber_mean": round(float(full[1]), 4),
            "eve_full_detect_rate": round(float(full[3]), 4), "trials_per_point": trials, "qubits_per_run": n}


# ---------------------------------------------------------------- fig 4: detection vs qubits
def fig_detection(trials: int) -> dict:
    ns = [16, 32, 64, 128, 256, 512]
    det, fa = [], []
    for n in ns:
        det.append(np.mean([bb84(n, eve_fraction=1.0, channel_error=0.02, seed=i).qber > THRESHOLD for i in range(trials)]))
        fa.append(np.mean([bb84(n, channel_error=0.02, seed=9000 + i).qber > THRESHOLD for i in range(trials)]))
    write_csv("data_detection_vs_qubits.csv", ["n_qubits", "detection_rate", "false_alarm_rate"],
              [[a, round(b, 3), round(c, 3)] for a, b, c in zip(ns, det, fa)])
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(ns, det, "o-", color=TEAL, label="eavesdropper detected")
    ax.plot(ns, fa, "s-", color=ORG, label="false alarm (no eavesdropper)")
    ax.set(xscale="log", xlabel="qubits sent", ylabel="rate", ylim=(-0.02, 1.05),
           title=f"More qubits = more reliable test ({trials} runs, 2% honest noise)")
    ax.set_xticks(ns); ax.set_xticklabels(ns); ax.legend(frameon=False)
    save(fig, "fig4_detection_vs_qubits.png")
    return {"detection_rate_by_qubits": dict(zip(map(str, ns), map(lambda v: round(float(v), 3), det)))}


# ---------------------------------------------------------------- fig 5: sizes
def fig_sizes() -> dict:
    xk = x25519.X25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    edk = ed25519.Ed25519PrivateKey.generate()
    rk = rsa.generate_private_key(65537, 2048)
    rpk = rk.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    pk, sk = pqc.sig_keygen(); sig = pqc.sign(sk, b"m")
    sizes = {"X25519 key share": len(xk), "ML-KEM-768 public key": len(ek), "ML-KEM-768 ciphertext": len(ct),
             "ML-KEM-768 secret key": len(dk), "Ed25519 public key": 32, "Ed25519 signature": len(edk.sign(b"m")),
             "RSA-2048 public key (DER)": len(rpk), "RSA-2048 signature": 256,
             "ML-DSA-65 public key": len(pk), "ML-DSA-65 secret key": len(sk), "ML-DSA-65 signature": len(sig)}
    write_csv("data_sizes_bytes.csv", ["item", "bytes"], [[k, v] for k, v in sizes.items()])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    def bars(a, labels, vals, cols, title, base):
        b = a.bar(labels, vals, color=cols)
        a.set_yscale("log"); a.set(title=title, ylabel="bytes (log scale)"); a.tick_params(axis="x", labelsize=8)
        for r, v in zip(b, vals):
            txt = f"{v:,} B" + ("" if v == base else f"\n{v / base:.0f}x")
            a.text(r.get_x() + r.get_width() / 2, v * 1.15, txt, ha="center", fontsize=8, color=DARK)
        a.set_ylim(10, max(vals) * 6)
    bars(ax[0], ["X25519\nkey share", "ML-KEM-768\npublic key", "ML-KEM-768\nciphertext"],
         [32, len(ek), len(ct)], [LAV, TEAL, TEAL], "Key exchange: what crosses the network", 32)
    bars(ax[1], ["Ed25519\nsignature", "RSA-2048\nsignature", "ML-DSA-65\nsignature"],
         [64, 256, len(sig)], [LAV, LAV, PUR], "Signatures: what crosses the network", 64)
    fig.suptitle("Post-quantum messages are bigger (sizes measured from our code; x = times the classical size)",
                 fontweight="bold", y=1.03)
    save(fig, "fig5_pqc_sizes.png")
    return sizes


# ---------------------------------------------------------------- fig 6: timing
def _time(fn, reps: int) -> tuple[float, float]:
    xs = []
    for _ in range(reps):
        t = time.perf_counter(); fn(); xs.append((time.perf_counter() - t) * 1000)
    return st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)


def fig_timing(reps: int) -> dict:
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    pk, sk = pqc.sig_keygen(); msg = b"isolate node 7"; sig = pqc.sign(sk, msg)
    ops = {"ML-KEM keygen": lambda: pqc.kem_keygen(), "ML-KEM encaps": lambda: pqc.kem_encaps(ek),
           "ML-KEM decaps": lambda: pqc.kem_decaps(dk, ct), "ML-DSA keygen": lambda: pqc.sig_keygen(),
           "ML-DSA sign": lambda: pqc.sign(sk, msg), "ML-DSA verify": lambda: pqc.verify(pk, msg, sig)}
    res = {k: _time(f, reps) for k, f in ops.items()}
    cx = x25519.X25519PrivateKey.generate(); peer = x25519.X25519PrivateKey.generate().public_key()
    edk = ed25519.Ed25519PrivateKey.generate(); esig = edk.sign(msg); epk = edk.public_key()
    rk = rsa.generate_private_key(65537, 2048); rsig = rk.sign(msg, __import__("cryptography").hazmat.primitives.asymmetric.padding.PKCS1v15(),
                                                            __import__("cryptography").hazmat.primitives.hashes.SHA256())
    classical = {"X25519 keygen": _time(lambda: x25519.X25519PrivateKey.generate(), reps),
                 "X25519 exchange": _time(lambda: cx.exchange(peer), reps),
                 "Ed25519 sign": _time(lambda: edk.sign(msg), reps), "Ed25519 verify": _time(lambda: epk.verify(esig, msg), reps),
                 "RSA-2048 keygen": _time(lambda: rsa.generate_private_key(65537, 2048), max(3, reps // 5))}
    write_csv("data_timing_ms.csv", ["operation", "mean_ms", "std_ms", "implementation"],
              [[k, round(v[0], 3), round(v[1], 3), "pure Python (educational)"] for k, v in res.items()] +
              [[k, round(v[0], 3), round(v[1], 3), "OpenSSL via cryptography (C)"] for k, v in classical.items()])
    fig, ax = plt.subplots(figsize=(9, 4.4))
    names = list(res); means = [res[k][0] for k in names]; sds = [res[k][1] for k in names]
    ax.bar(names, means, yerr=sds, capsize=3, color=[TEAL] * 3 + [PUR] * 3)
    for i, v in enumerate(means):
        ax.text(i, v + max(means) * 0.02, f"{v:.1f} ms", ha="center", fontsize=8)
    ax.set(ylabel="milliseconds", title=f"ML-KEM-768 and ML-DSA-65 operation time (mean of {reps} runs)")
    ax.tick_params(axis="x", labelsize=8)
    fig.text(0.5, -0.03, "Pure-Python educational code. Optimised C implementations (liboqs, OpenSSL 3.5+) are far faster, "
             "so compare sizes, not these timings, with classical crypto.", ha="center", fontsize=8, color=LAV)
    save(fig, "fig6_pqc_timing.png")
    return {k: round(v[0], 2) for k, v in {**res, **classical}.items()}


# ---------------------------------------------------------------- fig 7: pipeline
def fig_pipeline(runs: int) -> dict:
    clean = [secure_channel("192.168.1.14", seed=100 + i) for i in range(runs)]
    eve = [secure_channel("192.168.1.14", eve_fraction=1.0, seed=300 + i) for i in range(runs)]
    ok = [r for r in clean if r["status"] == "secure_channel_established"]
    phases = ["qrng_ms", "bb84_ms", "ml_kem_ms", "hkdf_aes_ms", "ml_dsa_ms"]
    means = [st.mean(r["timings_ms"][p] for r in ok) for p in phases]
    write_csv("data_pipeline_runs.csv", ["scenario", "run", "status", "qber", "total_ms"],
              [["clean", i, r["status"], r["qber"], r["key_gen_time_ms"]] for i, r in enumerate(clean)] +
              [["eavesdropper", i, r["status"], r["qber"], r["key_gen_time_ms"]] for i, r in enumerate(eve)])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1.6, 1]})
    left = 0
    for p, m, c in zip(phases, means, [PUR, ORG, TEAL, GOLD, LAV]):
        ax[0].barh(["Stage 2\n(clean run)"], [m], left=left, color=c, label=f"{p[:-3].replace('_', '-')}: {m:.1f} ms")
        left += m
    ax[0].set(xlabel="milliseconds", title=f"Where the time goes (mean of {len(ok)} successful runs, total {left:.0f} ms)")
    ax[0].legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.25)); ax[0].grid(False)
    bp = ax[1].boxplot([[r["key_gen_time_ms"] for r in clean], [r["key_gen_time_ms"] for r in eve]],
                       tick_labels=["secure channel\nestablished", "eavesdropper\n(aborted)"], patch_artist=True)
    for patch, c in zip(bp["boxes"], [TEAL, ORG]):
        patch.set_facecolor(c); patch.set_alpha(0.5)
    ax[1].set(ylabel="milliseconds", title="Total time per run")
    save(fig, "fig7_pipeline_latency.png")
    return {"runs": runs, "clean_established": len(ok), "eve_aborted": sum(r["status"] == "aborted_eavesdrop_detected" for r in eve),
            "mean_total_ms_clean": round(st.mean(r["key_gen_time_ms"] for r in ok), 1),
            "phase_mean_ms": dict(zip(phases, map(lambda v: round(v, 1), means)))}


# ---------------------------------------------------------------- attack tests + scorecard
def attack_tests() -> list[tuple[str, bool]]:
    out = []
    pk, sk = pqc.sig_keygen(); sig = pqc.sign(sk, b"isolate node 7")
    out.append(("Edited message under a valid signature", not pqc.verify(pk, b"reconnect node 7", sig)))
    out.append(("Edited signature bytes", not pqc.verify(pk, b"isolate node 7", bytes([sig[0] ^ 1]) + sig[1:])))
    out.append(("Signature checked with the wrong key", not pqc.verify(pqc.sig_keygen()[0], b"isolate node 7", sig)))
    s = CommandSigner(); v = CommandVerifier(s.public_key)
    c = s.sign("n1", "isolate"); v.verify(c)
    out.append(("Replayed command", v.verify(c)[1] == "replay_detected"))
    f = s.sign("n1", "isolate"); f["payload"]["action"] = "reconnect"
    out.append(("Forged 'reconnect' order", v.verify(f)[1] == "bad_signature"))
    out.append(("Command from an attacker's key", CommandVerifier(s.public_key).verify(CommandSigner().sign("n1", "reconnect"))[1] == "bad_signature"))
    out.append(("Stale command (old timestamp)", CommandVerifier(s.public_key).verify(s.sign("n1", "isolate", now=1.0))[1] == "stale_command"))
    out.append(("Action outside the allowlist", CommandVerifier(s.public_key).verify(s.sign("n1", "format_disk"))[1] == "action_not_allowed"))
    key = derive_session_key(b"a" * 32, b"b" * 32, b"n"); blob = encrypt(key, b"data", b"n")
    try:
        decrypt(key, blob[:-1] + bytes([blob[-1] ^ 1]), b"n"); ok = False
    except InvalidTag:
        ok = True
    out.append(("Edited encrypted traffic (AES-GCM)", ok))
    ek, dk = pqc.kem_keygen(); ss, ct = pqc.kem_encaps(ek)
    out.append(("Edited ML-KEM ciphertext", pqc.kem_decaps(dk, bytes([ct[0] ^ 1]) + ct[1:]) != ss))
    return out


def fig_scorecard(S: dict, attacks: list[tuple[str, bool]]) -> None:
    fig = plt.figure(figsize=(12.5, 6.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 12.5); ax.set_ylim(0, 6.4)
    ax.text(0.4, 6.0, "Stage 2 results scorecard", fontsize=17, fontweight="bold", color=DARK)
    ax.text(0.4, 5.62, f"All numbers measured by experiments/run_all.py on {SUMMARY['machine']['platform']}", fontsize=8.5, color=LAV)
    q, d, p, z = S["qber"], S["detection"], S["pipeline"], S["qrng"]
    tiles = [(f"{q['clean_qber_mean']:.0%}", "QBER, clean channel", TEAL),
             (f"{q['eve_full_qber_mean']:.0%}", "QBER, full eavesdropper\n(theory: 25%)", ORG),
             (f"{q['eve_full_detect_rate']:.0%}", f"eavesdropper runs flagged\n({q['trials_per_point']} runs, {q['qubits_per_run']} qubits)", ORG),
             (f"{p['clean_established']}/{p['runs']}", "clean runs: channel\nestablished", TEAL),
             (f"{p['eve_aborted']}/{p['runs']}", "eavesdropper runs:\naborted safely", ORG),
             (f"{p['mean_total_ms_clean'] / 1000:.2f} s", "mean time to secure\nchannel (simulated)", PUR),
             ("PASS" if z["all_pass"] else "FAIL", f"QRNG randomness checks\n({z['bytes']:,} bytes)", TEAL if z["all_pass"] else ORG),
             (f"{sum(a for _, a in attacks)}/{len(attacks)}", "attack tests rejected", TEAL)]
    for i, (big, small, col) in enumerate(tiles):
        x, y = 0.4 + (i % 4) * 1.75, 3.55 - (i // 4) * 1.75
        ax.add_patch(plt.Rectangle((x, y), 1.6, 1.55, color=col, alpha=0.12, lw=0)); ax.add_patch(plt.Rectangle((x, y + 1.45), 1.6, 0.1, color=col, lw=0))
        ax.text(x + 0.8, y + 0.98, big, ha="center", va="center", fontsize=19, fontweight="bold", color=col)
        ax.text(x + 0.8, y + 0.36, small, ha="center", va="center", fontsize=7.5, color=DARK)
    ax.text(7.7, 5.0, "Attacks tried against our code", fontsize=11, fontweight="bold", color=DARK)
    for i, (name, ok) in enumerate(attacks):
        y = 4.6 - i * 0.42
        ax.text(7.7, y, "REJECTED" if ok else "ACCEPTED!", fontsize=8, fontweight="bold", color=TEAL if ok else ORG, va="center")
        ax.text(8.75, y, name, fontsize=8.5, color=DARK, va="center")
    ax.text(0.4, 0.25, "Honest limits: QRNG and BB84 are simulated in Qiskit; ML-KEM/ML-DSA run in educational pure Python (not for production).",
            fontsize=8, color=LAV)
    save(fig, "fig8_scorecard.png", tight=False)


# ---------------------------------------------------------------- RESULTS.md
def write_results_md(S: dict, attacks) -> None:
    sz = S["sizes"]
    md = f"""# Stage 2 Results

Generated by `python -m experiments.run_all` ({'quick mode' if S['quick'] else 'full mode'}). Machine: {S['machine']['platform']}, Python {S['machine']['python']}, Qiskit {S['machine']['qiskit']}.

![scorecard](fig8_scorecard.png)

## 1. Architecture
![architecture](fig0_architecture.png)

## 2. QRNG quality (simulated)
![qrng](fig1_qrng_quality.png)

Monobit p = {S['qrng']['monobit_p']}, chi-square z = {S['qrng']['chi2_z']}, serial correlation r = {S['qrng']['serial_r']}. These are basic sanity checks, not the full NIST SP 800-22 suite.
The simulator's randomness is pseudo-random; this demonstrates the circuit and workflow only.

## 3. BB84
![walkthrough](fig2_bb84_walkthrough.png)
![qber](fig3_qber_experiments.png)
![detection](fig4_detection_vs_qubits.png)

| Measurement | Value |
|---|---|
| Mean QBER, clean channel | {S['qber']['clean_qber_mean']:.4f} |
| Mean QBER, Eve intercepts every qubit | {S['qber']['eve_full_qber_mean']:.4f} (theory 0.25) |
| Eavesdropper runs flagged (full interception) | {S['qber']['eve_full_detect_rate']:.0%} |

Reading the charts: a partial eavesdropper who touches less than about 44% of the qubits stays under the 11% limit (0.25 x 0.44 = 0.11), so the threshold alone does not catch her. In our pipeline such a run still aborts, because the two keys no longer match (we do not implement error correction).

## 4. Post-quantum sizes and speed
![sizes](fig5_pqc_sizes.png)
![timing](fig6_pqc_timing.png)

Sizes are exact. Timings are from pure-Python educational code and are NOT comparable with C implementations.

| Item | Bytes |
|---|---|
""" + "\n".join(f"| {k} | {v:,} |" for k, v in sz.items()) + f"""

## 5. End-to-end pipeline
![pipeline](fig7_pipeline_latency.png)

Mean phase times (ms): {S['pipeline']['phase_mean_ms']}.

## 6. Attack tests
| Attack | Result |
|---|---|
""" + "\n".join(f"| {n} | {'rejected' if ok else 'ACCEPTED (bug)'} |" for n, ok in attacks) + "\n"
    (OUT / "RESULTS.md").write_text(md)
    print("  saved RESULTS.md")


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    q = a.quick
    OUT.mkdir(exist_ok=True)
    import qiskit
    SUMMARY.update(quick=q, machine={"platform": f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPUs",
                                     "python": platform.python_version(), "qiskit": qiskit.__version__})
    print("Stage 2 experiments", "(quick)" if q else "(full)")
    fig_architecture()
    SUMMARY["qrng"] = fig_qrng(1024 if q else 4096)
    fig_bb84_walkthrough()
    SUMMARY["qber"] = fig_qber(6 if q else 20, 512 if q else 1024)
    SUMMARY["detection"] = fig_detection(20 if q else 100)
    SUMMARY["sizes"] = fig_sizes()
    SUMMARY["timing_ms"] = fig_timing(5 if q else 20)
    SUMMARY["pipeline"] = fig_pipeline(5 if q else 20)
    attacks = attack_tests()
    SUMMARY["attacks"] = {n: ok for n, ok in attacks}
    fig_scorecard(SUMMARY, attacks)
    (OUT / "summary.json").write_text(json.dumps(SUMMARY, indent=2, default=str))
    write_results_md(SUMMARY, attacks)
    print("Done. Open results/RESULTS.md")


if __name__ == "__main__":
    main()
```
**RUN a fast version first** (about 30 seconds):
```bash
python -m experiments.run_all --quick
```
**Then the full version** (about 5 to 8 minutes; let it finish):
```bash
python -m experiments.run_all
```
**View the results:** in the Explorer open `results/`, click any `.png`. To see everything on one page, open `results/RESULTS.md` and press `Ctrl+Shift+V`.

---

# PART 5: Understand your results

| File in `results/` | What it shows | One sentence for your report |
|---|---|---|
| `fig0_architecture.png` | The Stage 2 pipeline | "QRNG seeds the PQC key generators, BB84 supplies a quantum key, ML-KEM and BB84 are mixed into one AES-256-GCM key, and ML-DSA signs events and commands." |
| `fig1_qrng_quality.png` | Byte histogram, random-bit image, three randomness checks | "The simulated QRNG passes monobit, chi-square and serial-correlation checks; these are sanity checks, not the full NIST suite." |
| `fig2_bb84_walkthrough.png` | 16 qubits traced step by step, clean vs eavesdropper | "Only matching-basis positions are kept; an eavesdropper creates errors among them." |
| `fig3_qber_experiments.png` | QBER vs eavesdropping, abort rate, and QBER vs honest noise | "Measured QBER follows the theory line 25% x interception; honest noise also raises QBER, so the threshold must be chosen carefully." |
| `fig4_detection_vs_qubits.png` | Detection and false-alarm rate vs number of qubits | "Short tests give unreliable decisions; detection becomes reliable at a few hundred qubits." |
| `fig5_pqc_sizes.png` | Key and signature sizes vs classical | "ML-KEM-768 public keys are 37 times larger than X25519 key shares; ML-DSA-65 signatures are 52 times larger than Ed25519." |
| `fig6_pqc_timing.png` | ML-KEM and ML-DSA operation times | "Timings are for pure-Python code and are only useful as relative costs between operations." |
| `fig7_pipeline_latency.png` | Where the time goes in one run | "BB84 simulation dominates run time; the PQC steps take a small share." |
| `fig8_scorecard.png` | All headline numbers and attack tests | "All 10 attacks against our code were rejected." |

## Numbers from the reference run
These came from one full run of this exact code (`Linux x86_64, 1 CPUs`, Python 3.12). **Yours will differ slightly.** Always report your own numbers from `results/summary.json`.

| Measurement | Reference run |
|---|---|
| QBER, clean channel | 0.0% |
| QBER, eavesdropper intercepts every qubit | 24.4% (theory: 25%) |
| Eavesdropper runs flagged (20 runs, 1024 qubits) | 100% |
| Detection rate at 16, 64, 128, 256 qubits | 51%, 80%, 96%, 100% |
| Clean runs that established a channel | 20/20 |
| Eavesdropper runs aborted before any key was used | 20/20 |
| Mean time to a secure channel | 701 ms (of which BB84 simulation 614 ms) |
| ML-KEM keygen, ML-DSA sign (pure Python) | 2.6 ms, 39.0 ms |
| QRNG monobit p-value | 0.808 (pass if above 0.01) |
| Attack tests rejected | 10/10 |

**Be careful with two claims.** Do not say "PQC is slower than RSA": our PQC is pure Python and RSA is optimised C, so the comparison is unfair. Compare **sizes**, which are exact. And do not say "true quantum randomness": our QRNG is simulated.

---

# PART 6: GitHub from VS Code (private repo, you are the leader)

Full detail and an error table are in `docs/GITHUB_SETUP.md`. The short path:

## 6.1 Create the private repo on GitHub
github.com → **+** → **New repository** → name `quantumshield-stage2` → **Private** → leave README, .gitignore and license **unticked** → **Create repository**.

## 6.2 Push from the VS Code terminal
```bash
git init -b main
git add .
git status
git commit -m "Stage 2: QRNG, BB84, ML-KEM, ML-DSA, tests and results"
git remote add origin https://github.com/YOUR-USERNAME/quantumshield-stage2.git
git push -u origin main
```
- **Check `git status` before committing.** `venv/` must **not** be listed (the `.gitignore` hides it).
- When Git asks for a password, paste a **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → tick `repo`). Your normal password no longer works.
- **Alternative:** the GitHub CLI: `gh auth login`, then `gh repo create quantumshield-stage2 --private --source=. --remote=origin --push`.

## 6.3 Use VS Code's Source Control panel (`Ctrl+Shift+G`)
Changed files are listed. Click **+** to stage, type a message, click the tick to commit, then **Sync Changes** to push.

## 6.4 Add your teammates
Repo → **Settings → Collaborators → Add people**. They must accept the email invite. Each teammate then runs `git clone <url>` and repeats Part 2 (venv and `pip install -r requirements.txt`).

## 6.5 The team workflow
```bash
git checkout main && git pull
git checkout -b stage2-your-task
# ...work, then:
python -m pytest -q
git add . && git commit -m "What you changed"
git push -u origin stage2-your-task
```
Open a **pull request**, let a teammate review, wait for CI (the green tick), then merge.

## 6.6 Branch protection: a correction
Requiring reviews before merge on a **private** repo needs a **paid plan** (GitHub Pro on a personal account, which students can get free through the GitHub Student Developer Pack). On the free plan, GitHub shows an upgrade message and enforces nothing. If you cannot enable it, make it a **team rule**: nobody pushes directly to `main`; everything goes through a reviewed pull request.

## 6.7 Tag your milestone
```bash
git tag v0.1-stage2
git push --tags
```

---

# PART 7: Problems and fixes

| Problem | Fix |
|---|---|
| `python` or `pip` not recognized | Windows: reinstall Python with "Add to PATH" ticked, reopen the terminal. Mac/Linux: use `python3` and `pip3`. |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, or use Git Bash or Command Prompt. |
| `No module named stage2` | Run from the project root (the folder containing `stage2/` and `pytest.ini`). |
| `No module named qiskit` (or `kyber_py`) | The venv is not active. Activate it (2.4) and select the interpreter (2.5). |
| `pip install` fails on a package | Check `python --version` is 3.11 or 3.12. Run `python -m pip install --upgrade pip`, then retry. |
| Python 3.13 or newer installed | Install 3.12 alongside it and create the venv with `py -3.12 -m venv venv`. |
| `run_all` seems stuck | It prints a line after each figure. The full run takes several minutes. Use `--quick` while developing. |
| A test fails once, then passes | BB84 is random. Run again; if it fails twice, read the `E` lines. |
| `git push` asks for a password and rejects it | Use a Personal Access Token, or `gh auth login`. |
| `failed to push some refs` | `git pull --rebase`, then push again. |
| Images do not show in `RESULTS.md` preview | Make sure `RESULTS.md` is inside `results/` next to the `.png` files. |

---

# PART 8: Final checklist

- [ ] `python -m pytest -q` shows `25 passed`.
- [ ] `python -m stage2.demo` shows the clean run, the aborted run, and the three command checks.
- [ ] `python -m experiments.run_all` finished and `results/` has 9 figures, CSV files, `summary.json` and `RESULTS.md`.
- [ ] You can draw BB84 from memory and explain why an eavesdropper causes about 25% error.
- [ ] You can explain why we use both quantum parts (simulated) and post-quantum parts (real standards).
- [ ] You can explain the three honest limits at the top of this guide.
- [ ] Your private GitHub repo has your code, the CI tick is green, and all teammates can clone it.
- [ ] You copied **your own** numbers from `results/summary.json` into your report.

## Your 30-second explanation of Stage 2
"Stage 2 turns the AI's alarm into a secure channel. A quantum random number generator makes the random seed. BB84 agrees a key and aborts if the error rate shows an eavesdropper. ML-KEM, a NIST post-quantum standard, establishes a second secret, and we mix both into one AES-256 key. ML-DSA signs every event and command, so a forged order is rejected. The quantum parts are simulated; the post-quantum parts follow the real standards."
