import type { SimulationStageId } from "@/types/quantumshield";

/**
 * Suggested FastAPI routes. Rename these to match your existing backend —
 * this is the only place paths are defined.
 */
export const ENDPOINTS = {
  overview: "/api/overview",
  threats: "/api/threats",
  crypto: "/api/crypto",
  healing: "/api/healing",
  topology: "/api/topology",
  pipeline: "/api/pipeline",
  logs: "/api/logs",
  simulationStage: (stage: SimulationStageId) => `/api/simulation/${stage}`,
} as const;
