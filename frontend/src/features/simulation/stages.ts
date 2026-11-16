import type { SimulationStageId } from "@/types/quantumshield";

/** The end-to-end workflow, in order. */
export const SIMULATION_STAGES: {
  id: SimulationStageId;
  label: string;
  description: string;
}[] = [
  { id: "traffic", label: "Network Traffic", description: "Capture & ingest flows" },
  { id: "detection", label: "AI Threat Detection", description: "Classify anomalies" },
  { id: "crypto", label: "Quantum-Safe Security", description: "Enforce PQC & rekey" },
  { id: "healing", label: "Self-Healing", description: "Isolate & reroute" },
  { id: "final", label: "Final Status", description: "Posture report" },
];
