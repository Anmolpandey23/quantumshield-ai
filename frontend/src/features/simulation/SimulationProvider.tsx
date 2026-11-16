import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { USE_MOCK_DATA } from "@/services/api/config";
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

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [stageStates, setStageStates] = useState(initialStates);
  const [results, setResults] = useState<SimulationContextValue["results"]>({});
  const [logs, setLogs] = useState<LogEntry[]>([]);
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
        toast.success("Simulation complete", {
          description: USE_MOCK_DATA
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
