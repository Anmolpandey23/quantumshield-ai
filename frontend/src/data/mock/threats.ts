import { createRng, pick, range } from "@/lib/seeded";
import type { RiskPoint, Severity, ThreatData, ThreatEvent } from "@/types/quantumshield";
import { isoMinusMinutes } from "./helpers";

/** DEMO DATA — synthetic threat events. Not real detections. */
const categories = [
  "DDoS Flood",
  "Port Scan",
  "Credential Stuffing",
  "Lateral Movement",
  "Data Exfiltration",
  "Malware Beacon",
  "Harvest-Now-Decrypt-Later",
  "DNS Tunneling",
];
const severities: Severity[] = ["critical", "high", "medium", "low"];
const statuses: ThreatEvent["status"][] = ["blocked", "mitigated", "monitoring", "investigating"];
const targets = ["core-1", "sw-b", "db", "app", "iot", "pqc-gw", "fw-2"];

function buildEvents(): ThreatEvent[] {
  const rng = createRng(7);
  return Array.from({ length: 28 }, (_, i) => {
    const sev = severities[Math.min(3, Math.floor(rng() * 4.4))] ?? "low";
    return {
      id: `THR-${(4821 - i).toString()}`,
      timestamp: isoMinusMinutes(i * 17 + Math.floor(rng() * 9)),
      category: pick(rng, categories),
      severity: sev,
      confidence: Math.round(range(rng, 0.71, 0.99) * 100) / 100,
      source: `${rng() > 0.5 ? "198.51.100" : "203.0.113"}.${Math.floor(range(rng, 2, 254))}`,
      target: pick(rng, targets),
      status: pick(rng, statuses),
    };
  });
}

function buildRisk(): RiskPoint[] {
  const rng = createRng(99);
  return Array.from({ length: 24 }, (_, i) => {
    const base = 32 + Math.sin(i / 2.6) * 14 + (i > 12 && i < 17 ? 26 : 0);
    return {
      hour: `${String(i).padStart(2, "0")}h`,
      predicted: Math.round(base + range(rng, -3, 3)),
      observed: i > 19 ? Number.NaN : Math.round(base + range(rng, -9, 9)),
    };
  });
}

export const mockThreatEvents = buildEvents();

export const mockThreats: ThreatData = {
  model: {
    name: "QS-ThreatNet (sample)",
    version: "v0.0-demo",
    architecture: "Temporal GNN + Transformer encoder",
    accuracy: 0.962,
    precision: 0.948,
    recall: 0.931,
    lastTrained: isoMinusMinutes(60 * 30),
  },
  currentRisk: 64,
  riskTrend: buildRisk(),
  categories: [
    { category: "DDoS", score: 72 },
    { category: "Intrusion", score: 58 },
    { category: "Malware", score: 41 },
    { category: "Exfiltration", score: 63 },
    { category: "Quantum HNDL", score: 49 },
    { category: "Insider", score: 27 },
  ],
  events: mockThreatEvents,
};
