import type {
  SimulationConfig,
  SimulationScenario,
  SimulationStageId,
  SimulationStageResult,
} from "@/types/quantumshield";

/** DEMO DATA — simulated stage outputs for the end-to-end workflow demo. */
export const scenarioLabels: Record<SimulationScenario, string> = {
  ddos: "Volumetric DDoS",
  lateral: "Lateral movement / ransomware",
  hndl: "Harvest-now, decrypt-later",
};

export function mockStageResult(
  stageId: SimulationStageId,
  config: SimulationConfig,
): SimulationStageResult {
  const k = config.intensity / 100;
  const flows = Math.round(18000 + 42000 * k);
  const scenario = scenarioLabels[config.scenario];
  switch (stageId) {
    case "traffic":
      return {
        stageId,
        headline: `Ingested ${flows.toLocaleString("en-US")} synthetic flows across ${config.nodes} nodes`,
        metrics: [
          { label: "Flows", value: flows.toLocaleString("en-US") },
          { label: "Peak Gbps", value: (2.4 + 7.1 * k).toFixed(1) },
          { label: "Nodes", value: String(config.nodes) },
        ],
        logs: [
          { level: "INFO", message: "Starting synthetic traffic generator (demo)" },
          { level: "INFO", message: `Scenario injected: ${scenario}` },
          { level: "SUCCESS", message: "Traffic capture window closed (5s)" },
        ],
      };
    case "detection":
      return {
        stageId,
        headline: `${scenario} detected with ${(0.86 + 0.12 * k).toFixed(2)} confidence`,
        metrics: [
          { label: "Malicious flows", value: Math.round(flows * 0.07 * k + 40).toLocaleString("en-US") },
          { label: "Confidence", value: (0.86 + 0.12 * k).toFixed(2) },
          { label: "Inference", value: `${Math.round(18 + 14 * k)} ms` },
        ],
        logs: [
          { level: "INFO", message: "Running AI threat model on feature batch" },
          { level: "WARN", message: `Anomaly cluster identified: ${scenario}` },
          { level: "SUCCESS", message: "Threat classified and forwarded to response layer" },
        ],
      };
    case "crypto":
      return {
        stageId,
        headline: "Affected tunnels re-keyed with ML-KEM-768 + ML-DSA-65",
        metrics: [
          { label: "Tunnels re-keyed", value: String(Math.round(6 + 10 * k)) },
          { label: "Handshake", value: `${(4.2 + 1.8 * k).toFixed(1)} ms` },
          { label: "Mode", value: config.scenario === "hndl" ? "PQC-only" : "Hybrid" },
        ],
        logs: [
          { level: "INFO", message: "Negotiating post-quantum key encapsulation (demo)" },
          { level: "SUCCESS", message: "Session keys rotated; classical fallback disabled for affected peers" },
        ],
      };
    case "healing":
      return {
        stageId,
        headline: `Isolated ${Math.max(1, Math.round(3 * k))} node(s) and rerouted traffic`,
        metrics: [
          { label: "Nodes isolated", value: String(Math.max(1, Math.round(3 * k))) },
          { label: "Paths rerouted", value: String(Math.round(2 + 5 * k)) },
          { label: "Time to heal", value: `${Math.round(24 + 30 * k)} s` },
        ],
        logs: [
          { level: "ERROR", message: "Node sw-b marked compromised — quarantining" },
          { level: "INFO", message: "Recomputing secure routes via core-2" },
          { level: "SUCCESS", message: "Service restored on fallback path" },
        ],
      };
    case "final":
      return {
        stageId,
        headline: "Network secured — simulated workflow completed",
        metrics: [
          { label: "Posture score", value: String(Math.round(92 - 8 * k)) },
          { label: "Residual risk", value: k > 0.7 ? "Medium" : "Low" },
          { label: "Availability", value: `${(99.99 - 0.3 * k).toFixed(2)}%` },
        ],
        logs: [{ level: "SUCCESS", message: "End-to-end simulation complete (demo data only)" }],
      };
  }
}
