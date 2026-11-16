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
