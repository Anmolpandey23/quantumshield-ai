import { motion } from "framer-motion";
import { BrainCircuit, CheckCircle2, HeartPulse, KeyRound, Loader2, Radio, ShieldCheck } from "lucide-react";
import { Fragment } from "react";
import { FlowArrow } from "@/components/hud/FlowArrow";
import { SIMULATION_STAGES } from "@/features/simulation/stages";
import { useSimulation } from "@/features/simulation/SimulationProvider";
import { cn } from "@/lib/utils";
import type { SimulationStageId } from "@/types/quantumshield";

const icons: Record<SimulationStageId, typeof Radio> = {
  traffic: Radio,
  detection: BrainCircuit,
  crypto: KeyRound,
  healing: HeartPulse,
  final: ShieldCheck,
};

/** Visual stepper of the end-to-end workflow, bound to the global simulation state. */
export function SimulationPipeline({ compact = false }: { compact?: boolean }) {
  const { stageStates, results } = useSimulation();

  return (
    <div className="flex flex-col gap-1 lg:flex-row lg:items-center lg:gap-1">
      {SIMULATION_STAGES.map((stage, i) => {
        const state = stageStates[stage.id];
        const Icon = icons[stage.id];
        const result = results[stage.id];
        return (
          <Fragment key={stage.id}>
            <motion.div
              layout
              className={cn(
                "relative w-full flex-1 self-stretch overflow-hidden rounded-lg border p-4 transition-colors",
                state === "pending" && "border-border bg-surface/40",
                state === "running" && "border-primary/60 bg-primary/10 glow",
                state === "done" && "border-success/40 bg-success/5",
              )}
            >
              {state === "running" && (
                <span className="pointer-events-none absolute inset-0 overflow-hidden">
                  <span className="absolute inset-x-0 h-1/2 animate-scan bg-gradient-to-b from-transparent via-primary/15 to-transparent" />
                </span>
              )}
              <div className="relative flex items-center gap-3">
                <span
                  className={cn(
                    "grid size-9 shrink-0 place-items-center rounded-md border",
                    state === "pending" && "border-border text-muted-foreground",
                    state === "running" && "border-primary text-primary",
                    state === "done" && "border-success/50 text-success",
                  )}
                >
                  {state === "running" ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : state === "done" ? (
                    <CheckCircle2 className="size-4" />
                  ) : (
                    <Icon className="size-4" />
                  )}
                </span>
                <div className="min-w-0">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    Step {i + 1}
                  </p>
                  <p className="font-display text-sm font-semibold leading-tight text-foreground">{stage.label}</p>
                </div>
              </div>
              {!compact && (
                <p className="relative mt-3 min-h-10 text-xs text-muted-foreground">
                  {result ? result.headline : state === "running" ? "Processing…" : stage.description}
                </p>
              )}
            </motion.div>
            {i < SIMULATION_STAGES.length - 1 && (
              <FlowArrow
                state={
                  state === "done"
                    ? stageStates[SIMULATION_STAGES[i + 1]?.id ?? stage.id] === "running"
                      ? "active"
                      : "done"
                    : "idle"
                }
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
