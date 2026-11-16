import { createRng, pick } from "@/lib/seeded";
import type { LogEntry, LogLevel } from "@/types/quantumshield";
import { isoMinusMinutes } from "./helpers";

/** DEMO DATA — sample execution logs. */
const templates: { level: LogLevel; module: string; message: string }[] = [
  { level: "INFO", module: "traffic_collector", message: "Captured 48,212 flows from edge taps (sample)" },
  { level: "DEBUG", module: "feature_engineering", message: "Computed 64-dim flow embeddings, batch=512" },
  { level: "WARN", module: "threat_model", message: "Inference queue above soft limit (1,820 > 1,500)" },
  { level: "SUCCESS", module: "pqc_engine", message: "ML-KEM-768 rekey completed for 12 tunnels" },
  { level: "INFO", module: "self_healing", message: "Health probe sweep complete: 13/14 nodes nominal" },
  { level: "ERROR", module: "self_healing", message: "Node sw-b failed integrity check — triggering isolation" },
  { level: "SUCCESS", module: "self_healing", message: "Traffic rerouted core-1 → core-2 → sw-b fallback path" },
  { level: "INFO", module: "threat_model", message: "Flagged 3 flows as Lateral Movement (conf ≥ 0.91)" },
  { level: "WARN", module: "pqc_engine", message: "Peer partner-gw.example negotiated classical-only suite" },
  { level: "DEBUG", module: "reporter", message: "Audit bundle written to reports/demo-audit.json" },
  { level: "INFO", module: "api_gateway", message: "GET /api/overview 200 (14ms)" },
  { level: "SUCCESS", module: "threat_model", message: "Blocked DDoS burst from 198.51.100.0/24" },
];

function build(): LogEntry[] {
  const rng = createRng(2026);
  return Array.from({ length: 60 }, (_, i) => {
    const t = pick(rng, templates);
    return { id: `log-${i}`, timestamp: isoMinusMinutes(i * 3 + rng() * 2), ...t };
  });
}

export const mockLogs: LogEntry[] = build();
export const logModules = Array.from(new Set(templates.map((t) => t.module))).sort();
