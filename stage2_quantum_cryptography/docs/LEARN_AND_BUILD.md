# Learn and Build Together: Stage 2 Session Plan

> **Main guide:** `docs/STEP_BY_STEP_VSCODE_GUIDE.md` has every command and file. This page is the shorter session plan and the answers to the research questions.

Yes, you can learn and build hand in hand. Each session below pairs a small piece of learning with a piece of code that already exists in this repo. The rule for every session:

1. **Predict**: write down what you think will happen.
2. **Run**: run the file or test.
3. **Compare**: if you were wrong, find out why. That gap is where learning happens.
4. **Log**: add one line to `docs/learning_log.md` (what you learned, what confused you).

Each session is about 2 to 4 hours. Total: about 2 to 3 weeks part-time. Resources are named, not linked, so search for them.

---

## Session 0: Setup (1 hour)
**Ladder topics:** none (tools only).
**Learn:** what a virtual environment is, what `pip install -r requirements.txt` does.
**Build:**
```bash
git clone <your-private-repo-url> && cd quantumshield-stage2
python3 -m venv venv && source venv/bin/activate        # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
python -m pytest -q
python -m stage2.demo
```
**Checkpoint:** `25 passed`, and the demo prints a clean run, an aborted run, and three command checks.
**If it fails:** run from the repo root, with `(venv)` showing in the prompt. `ModuleNotFoundError: stage2` means you are in the wrong folder.

## Session 1: Basic cryptography (ladder #1)
**Learn:** symmetric vs public-key, hash, key exchange, signature. Why AES encrypts the data and public-key methods only agree on keys. (Boneh, *Cryptography I*, or the free Boneh and Shoup textbook: first chapters on ciphers and authenticated encryption.)
**Build:** read `stage2/channel.py` (30 lines) and `tests/test_channel.py`.
**Predict, then test:** change one byte of an encrypted message in a Python shell and decrypt. What happens? (AES-GCM raises `InvalidTag`.)
**Self-test:** Why is the nonce 12 random bytes? Why do we pass `aad`? What does HKDF do?

## Session 2: Qubits and Qiskit (ladder #2, #3)
**Learn:** qubit, superposition, measurement, the X and H gates, how Qiskit builds and runs a circuit. (IBM Quantum Learning, "Basics of quantum information"; Qiskit docs.)
**Build:** run the three exercises and predict each result first.
```bash
python exercises/01_hello_qubit.py      # about 500/500
python exercises/02_basis_intuition.py  # right basis: certain; wrong basis: coin flip
```
**Checkpoint:** you can explain why test B in exercise 2 is random but test C is not.

## Session 3: QRNG (ladder #4)
**Learn:** why measuring a superposed qubit gives a random bit; why that is different from a formula-based generator.
**Build:** read `stage2/qrng.py`, then:
```bash
python -m pytest tests/test_qrng.py -v
python -m experiments.run_all --quick     # look at results/fig1_qrng_quality.png
```
**Honest point to write in your log:** on a simulator the randomness is pseudo-random. The code shows the circuit and workflow only. Real randomness needs real hardware.
**Self-test:** What do the monobit, chi-square and serial tests check? Why does passing them not prove security?

## Session 4: BB84 and no-cloning (ladder #5, #6)
**Learn:** bases, sifting, QBER, intercept-resend attack, why Eve causes about 25% error, why around 11% is the limit. (Shor and Preskill 2000; Gisin et al. 2002 for the big picture.) Also: the no-cloning theorem.
**Build:**
```bash
python exercises/03_eve_by_hand.py        # predict the numbers first
python -m pytest tests/test_bb84.py -v
```
Open `results/fig2_bb84_walkthrough.png` and trace the 16 qubits by hand. Then read `stage2/bb84.py`.
**Try:** set `eve_fraction=0.3`. Why is she not caught by the 11% rule? (0.25 x 0.3 = 7.5%.)
**Self-test:** Draw BB84 from memory, including who announces what in public.

## Session 5: Why post-quantum? Shor, Grover, lattices (ladder #7, #8, #9)
**Learn:** Shor breaks RSA and ECC; Grover only halves symmetric strength, so use AES-256. NIST standardised ML-KEM (FIPS 203), ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) in 2024. Lattice idea: solving noisy equations is hard.
**Build:** open `results/fig5_pqc_sizes.png`. Notice how much bigger PQC keys and signatures are than X25519 and Ed25519.
**Self-test:** What does the size increase mean for network traffic, and for an intrusion detector trained on classical traffic (your Stage 1)?

## Session 6: KEM, signatures and signed commands (ladder #10, #11, #12)
**Learn:** keygen, encapsulate, decapsulate; sign and verify. What is implicit rejection in ML-KEM? (A tampered ciphertext gives a different secret, not an error.)
**Build:**
```bash
python -m pytest tests/test_pqc.py tests/test_commands.py -v
```
Read `stage2/pqc.py` and `stage2/commands.py`. Then break a command on purpose in a Python shell and see which rule rejects it.
**Optional (ladder #12):** install liboqs and swap the backend in `stage2/pqc.py`. This is the production path. Use WSL on Windows, and pin a version.
**Self-test:** How does a verifier stop a replayed command? A forged one? A command outside the allowlist?

## Session 7: Put it together and know the limits (ladder #13, #14)
**Learn:** hybrid key exchange (mix classical or QKD material with ML-KEM), "harvest now, decrypt later", and what is simulated vs real.
**Build:**
```bash
python -m stage2.demo
python -m experiments.run_all             # full run; makes every figure and RESULTS.md
```
**Checkpoint:** you can explain each box of `results/fig0_architecture.png` and each number on `results/fig8_scorecard.png`.

## Session 8: Ship it
Open a pull request, get a teammate review, merge, tag `v0.1-stage2`. Copy the numbers from `results/summary.json` into your report. See `docs/GITHUB_SETUP.md`.

---

# Your research questions, answered

1. **Why both quantum and post-quantum parts?** QRNG and BB84 demonstrate quantum key material and eavesdrop detection, but real QKD needs photons and hardware. ML-KEM and ML-DSA are classical algorithms that resist quantum attacks and work on normal computers today, so they protect real traffic. In this project the quantum parts are simulated; the post-quantum parts are real standards.
2. **How does QRNG output feed key creation?** `pqc.seed_from_qrng()` seeds the ML-KEM and ML-DSA key generators with QRNG bytes, and BB84 output is mixed into the session key with HKDF (`channel.derive_session_key`).
3. **What QBER do we expect?** About 0% on a clean channel, about 25% when Eve intercepts everything, and we abort above 11%.
4. **Kyber768 vs ML-KEM-768?** ML-KEM-768 is the final NIST standard. It is not interoperable with the earlier Kyber round-3 version, so use the ML-KEM name and code.
5. **Key sizes?** ML-KEM-768: 1,184 B public key, 1,088 B ciphertext, 32 B secret. ML-DSA-65: 1,952 B public key, 3,309 B signature. Exact numbers are in `results/data_sizes_bytes.csv`.
6. **Timing against RSA?** See `results/data_timing_ms.csv`. Our PQC code is pure Python, so only compare sizes fairly. Use liboqs or OpenSSL 3.5+ for fair speed tests.
