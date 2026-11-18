/**
 * QuantumShield service layer — the single integration seam between the UI
 * and your Python backend. Every page reads data through these functions.
 *
 * While USE_MOCK_DATA is true, bundled demo data is returned.
 * Flip VITE_USE_MOCK_DATA=false to call FastAPI via ENDPOINTS instead.
 */
import { mockCrypto } from "@/data/mock/crypto";
import { mockHealing } from "@/data/mock/healing";
import { mockLogs } from "@/data/mock/logs";
import { mockOverview } from "@/data/mock/overview";
import { mockPipeline } from "@/data/mock/pipeline";
import { mockStageResult } from "@/data/mock/simulation";
import { mockThreats } from "@/data/mock/threats";
import { mockTopology } from "@/data/mock/topology";
import type {
  CryptoData,
  HealingData,
  LogEntry,
  OverviewData,
  PipelineData,
  SimulationConfig,
  SimulationStageId,
  SimulationStageResult,
  ThreatData,
  Topology,
} from "@/types/quantumshield";
import { apiClient } from "./api/client";
import { isLiveFeedActive } from "./api/config";
import { ENDPOINTS } from "./api/endpoints";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

function source<T>(mock: T, path: string): () => Promise<T> {
  return async () => (isLiveFeedActive() ? apiClient.get<T>(path) : mock);
}

export const quantumShieldService = {
  getOverview: source<OverviewData>(mockOverview, ENDPOINTS.overview),
  getThreats: source<ThreatData>(mockThreats, ENDPOINTS.threats),
  getCrypto: source<CryptoData>(mockCrypto, ENDPOINTS.crypto),
  getHealing: source<HealingData>(mockHealing, ENDPOINTS.healing),
  getTopology: source<Topology>(mockTopology, ENDPOINTS.topology),
  getPipeline: source<PipelineData>(mockPipeline, ENDPOINTS.pipeline),
  getLogs: source<LogEntry[]>(mockLogs, ENDPOINTS.logs),

  /** Runs one stage of the end-to-end workflow. Demo mode adds an artificial delay. */
  async runSimulationStage(
    stage: SimulationStageId,
    config: SimulationConfig,
  ): Promise<SimulationStageResult> {
    if (!isLiveFeedActive()) {
      await wait(stage === "final" ? 900 : 1600);
      return mockStageResult(stage, config);
    }
    return apiClient.post<SimulationStageResult>(ENDPOINTS.simulationStage(stage), config);
  },

  /** Restores and reconnects isolated nodes via the live PQC re-keying verification cycle. */
  async restoreIsolated(nodeId?: string): Promise<{ reconnected: string[]; remaining_isolated: number }> {
    if (!isLiveFeedActive()) {
      return { reconnected: [], remaining_isolated: 0 };
    }
    return apiClient.post<{ reconnected: string[]; remaining_isolated: number }>(
      "/api/healing/restore" + (nodeId ? `?node_id=${encodeURIComponent(nodeId)}` : ""),
      {},
    );
  },
};
