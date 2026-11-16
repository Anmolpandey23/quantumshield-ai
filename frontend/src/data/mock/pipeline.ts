import { createRng, range } from "@/lib/seeded";
import type { PipelineData } from "@/types/quantumshield";

/** DEMO DATA — sample pipeline telemetry. */
const stages: PipelineData["stages"] = [
  { id: "ingest", name: "Traffic Ingestion", module: "traffic_collector.py", status: "running", throughput: 12400, latencyMs: 3, queue: 120, uptime: 99.98 },
  { id: "features", name: "Feature Extraction", module: "feature_engineering.py", status: "running", throughput: 11800, latencyMs: 7, queue: 340, uptime: 99.95 },
  { id: "inference", name: "AI Threat Inference", module: "threat_model.py", status: "degraded", throughput: 9600, latencyMs: 24, queue: 1820, uptime: 99.41 },
  { id: "pqc", name: "PQC Enforcement", module: "pqc_engine.py", status: "running", throughput: 9400, latencyMs: 5, queue: 90, uptime: 99.99 },
  { id: "healing", name: "Self-Healing Orchestrator", module: "self_healing.py", status: "running", throughput: 410, latencyMs: 38, queue: 4, uptime: 99.9 },
  { id: "report", name: "Reporting & Audit", module: "reporter.py", status: "idle", throughput: 120, latencyMs: 12, queue: 0, uptime: 100 },
];

function buildHistory() {
  const rng = createRng(1234);
  return Array.from({ length: 20 }, (_, i) => {
    const row: PipelineData["throughputHistory"][number] = { time: `T-${19 - i}m` };
    for (const s of stages.slice(0, 4)) {
      row[s.id] = Math.round(s.throughput * range(rng, 0.82, 1.08));
    }
    return row;
  });
}

export const mockPipeline: PipelineData = { stages, throughputHistory: buildHistory() };
