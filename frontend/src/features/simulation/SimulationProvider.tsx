import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { mockStageResult } from "@/data/mock/simulation";
import { isLiveFeedActive } from "@/services/api/config";
import { quantumShieldService } from "@/services/quantumshield.service";
import type {
  LogEntry,
  SimulationConfig,
  SimulationStageId,
  SimulationStageResult,
} from "@/types/quantumshield";
import { SIMULATION_STAGES } from "./stages";

export type StageState = "pending" | "running" | "done";
export type RunStatus = "idle" | "running" | "complete" | "error";

interface SimulationContextValue {
  status: RunStatus;
  activeIndex: number;
  stageStates: Record<SimulationStageId, StageState>;
  results: Partial<Record<SimulationStageId, SimulationStageResult>>;
  logs: LogEntry[];
  config: SimulationConfig;
  progress: number;
  setConfig: (c: Partial<SimulationConfig>) => void;
  run: () => void;
  reset: () => void;
}

const SimulationContext = createContext<SimulationContextValue | null>(null);

const initialStates = () =>
  Object.fromEntries(SIMULATION_STAGES.map((s) => [s.id, "pending"])) as Record<
    SimulationStageId,
    StageState
  >;

const defaultDoneStates = () =>
  Object.fromEntries(SIMULATION_STAGES.map((s) => [s.id, "done"])) as Record<
    SimulationStageId,
    StageState
  >;

const defaultInitialResults = (): Record<SimulationStageId, SimulationStageResult> => {
  const cfg: SimulationConfig = { scenario: "lateral", intensity: 60, nodes: 14 };
  return {
    traffic: mockStageResult("traffic", cfg),
    detection: mockStageResult("detection", cfg),
    crypto: mockStageResult("crypto", cfg),
    healing: mockStageResult("healing", cfg),
    final: mockStageResult("final", cfg),
  };
};

const defaultInitialLogs = (): LogEntry[] => [
  { id: "init-1", timestamp: new Date(Date.now() - 14000).toISOString(), level: "INFO", module: "sim.traffic", message: "Synthetic packet stream captured: 43,200 flows across 14 nodes" },
  { id: "init-2", timestamp: new Date(Date.now() - 11000).toISOString(), level: "WARN", module: "sim.detection", message: "Lateral movement / ransomware detected (risk 0.93)" },
  { id: "init-3", timestamp: new Date(Date.now() - 8000).toISOString(), level: "SUCCESS", module: "sim.crypto", message: "Tunnels re-keyed with ML-KEM-768 (1,088 B ciphertext)" },
  { id: "init-4", timestamp: new Date(Date.now() - 5000).toISOString(), level: "SUCCESS", module: "sim.healing", message: "ML-DSA-65 digitally signed isolation command verified (3,309 B signature)" },
  { id: "init-5", timestamp: new Date(Date.now() - 2000).toISOString(), level: "SUCCESS", module: "sim.healing", message: "Quarantined 2 nodes, rerouted encrypted paths via quantum-safe mesh" },
  { id: "init-6", timestamp: new Date().toISOString(), level: "SUCCESS", module: "sim.final", message: "Attack fully mitigated in 94 ms · Fleet posture 100% verified" },
];

export function SimulationProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<RunStatus>("complete");
  const [activeIndex, setActiveIndex] = useState(SIMULATION_STAGES.length);
  const [stageStates, setStageStates] = useState(defaultDoneStates);
  const [results, setResults] = useState<SimulationContextValue["results"]>(defaultInitialResults);
  const [logs, setLogs] = useState<LogEntry[]>(defaultInitialLogs);
  const [config, setConfigState] = useState<SimulationConfig>({
    scenario: "lateral",
    intensity: 60,
    nodes: 14,
  });
  const runId = useRef(0);

  const setConfig = useCallback(
    (c: Partial<SimulationConfig>) => setConfigState((prev) => ({ ...prev, ...c })),
    [],
  );

  const reset = useCallback(() => {
    runId.current += 1;
    setStatus("idle");
    setActiveIndex(-1);
    setStageStates(initialStates());
    setResults({});
    setLogs([]);
  }, []);

  const run = useCallback(() => {
    const id = ++runId.current;
    const cfg = config;
    setStatus("running");
    setStageStates(initialStates());
    setResults({});
    setLogs([]);

    (async () => {
      try {
        for (const [i, stage] of SIMULATION_STAGES.entries()) {
          if (runId.current !== id) return;
          setActiveIndex(i);
          setStageStates((s) => ({ ...s, [stage.id]: "running" }));
          const result = await quantumShieldService.runSimulationStage(stage.id, cfg);
          if (runId.current !== id) return;
          setResults((r) => ({ ...r, [stage.id]: result }));
          setStageStates((s) => ({ ...s, [stage.id]: "done" }));
          void queryClient.invalidateQueries();
          setLogs((prev) => [
            ...prev,
            ...result.logs.map((l, j) => ({
              id: `sim-${i}-${j}-${id}`,
              timestamp: new Date().toISOString(),
              level: l.level,
              module: `sim.${stage.id}`,
              message: l.message,
            })),
          ]);
        }
        setStatus("complete");
        setActiveIndex(SIMULATION_STAGES.length);
        void queryClient.invalidateQueries();
        toast.success("Simulation complete", {
          description: !isLiveFeedActive()
            ? "Demo workflow finished. Results are simulated, not real security data."
            : "Scenario finished. Synthetic attacks were run through the real Stage 2 to 4 pipeline.",
        });
      } catch (err) {
        if (runId.current !== id) return;
        setStatus("error");
        toast.error("Simulation failed", {
          description: err instanceof Error ? err.message : "Unknown error",
        });
      }
    })();
  }, [config]);

  const doneCount = Object.values(stageStates).filter((s) => s === "done").length;
  const progress = Math.round((doneCount / SIMULATION_STAGES.length) * 100);

  const value = useMemo(
    () => ({ status, activeIndex, stageStates, results, logs, config, progress, setConfig, run, reset }),
    [status, activeIndex, stageStates, results, logs, config, progress, setConfig, run, reset],
  );

  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>;
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulation must be used inside <SimulationProvider>");
  return ctx;
}
