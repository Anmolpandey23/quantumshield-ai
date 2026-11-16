import type { CryptoData } from "@/types/quantumshield";
import { isoMinusMinutes } from "./helpers";

/** DEMO DATA — illustrative values. Benchmarks are not real measurements. */
export const mockCrypto: CryptoData = {
  coverage: 78,
  algorithms: [
    { id: "mlkem", name: "ML-KEM-768", family: "CRYSTALS-Kyber", role: "Key Encapsulation", standard: "FIPS 203", securityLevel: 3, status: "active", publicKeyBytes: 1184, usage: 82 },
    { id: "mldsa", name: "ML-DSA-65", family: "CRYSTALS-Dilithium", role: "Digital Signature", standard: "FIPS 204", securityLevel: 3, status: "active", publicKeyBytes: 1952, usage: 74 },
    { id: "slhdsa", name: "SLH-DSA-128s", family: "SPHINCS+", role: "Digital Signature", standard: "FIPS 205", securityLevel: 1, status: "standby", publicKeyBytes: 32, usage: 12 },
    { id: "falcon", name: "FN-DSA-512", family: "Falcon", role: "Digital Signature", standard: "Draft", securityLevel: 1, status: "testing", publicKeyBytes: 897, usage: 6 },
  ],
  sessions: [
    { id: "s-01", peer: "app-cluster.internal", kem: "ML-KEM-768", signature: "ML-DSA-65", mode: "hybrid", established: isoMinusMinutes(3), latencyMs: 4.8 },
    { id: "s-02", peer: "datastore.internal", kem: "ML-KEM-768", signature: "ML-DSA-65", mode: "pqc-only", established: isoMinusMinutes(9), latencyMs: 5.6 },
    { id: "s-03", peer: "soc-console.internal", kem: "X25519+ML-KEM", signature: "ECDSA+ML-DSA", mode: "hybrid", established: isoMinusMinutes(14), latencyMs: 3.9 },
    { id: "s-04", peer: "partner-gw.example", kem: "X25519", signature: "ECDSA P-256", mode: "classical", established: isoMinusMinutes(22), latencyMs: 2.1 },
    { id: "s-05", peer: "iot-hub.internal", kem: "ML-KEM-512", signature: "FN-DSA-512", mode: "pqc-only", established: isoMinusMinutes(31), latencyMs: 6.3 },
  ],
  benchmarks: [
    { operation: "KeyGen", classicalMs: 0.06, pqcMs: 0.09 },
    { operation: "Encaps", classicalMs: 0.07, pqcMs: 0.11 },
    { operation: "Decaps", classicalMs: 0.07, pqcMs: 0.1 },
    { operation: "Sign", classicalMs: 0.12, pqcMs: 0.31 },
    { operation: "Verify", classicalMs: 0.18, pqcMs: 0.09 },
  ],
  rotations: [
    { id: "r1", timestamp: isoMinusMinutes(12), algorithm: "ML-KEM-768", scope: "Core ↔ App cluster" },
    { id: "r2", timestamp: isoMinusMinutes(74), algorithm: "ML-DSA-65", scope: "Firmware signing" },
    { id: "r3", timestamp: isoMinusMinutes(190), algorithm: "ML-KEM-768", scope: "Datastore tunnel" },
    { id: "r4", timestamp: isoMinusMinutes(410), algorithm: "FN-DSA-512", scope: "IoT segment (pilot)" },
  ],
};
