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
