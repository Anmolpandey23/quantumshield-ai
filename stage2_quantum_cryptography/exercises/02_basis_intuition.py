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
