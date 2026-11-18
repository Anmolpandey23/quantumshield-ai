import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Crosshair, FileCheck2, FlaskConical, KeyRound, Radio, Settings2, ShieldAlert, ShieldCheck, TerminalSquare } from "lucide-react";
import { useEffect, useRef } from "react";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { StatusBadge } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { RunSimulationButton } from "@/components/simulation/RunSimulationButton";
import { SimulationPipeline } from "@/components/simulation/SimulationPipeline";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ShineBorder } from "@/components/ui/shine-border";
import { Slider } from "@/components/ui/slider";
import { scenarioLabels } from "@/data/mock/simulation";
import { SIMULATION_STAGES } from "@/features/simulation/stages";
import { useSimulation } from "@/features/simulation/SimulationProvider";
import { fmtTime } from "@/lib/format";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { cn } from "@/lib/utils";
import type { LogLevel, SimulationScenario } from "@/types/quantumshield";

export const Route = createFileRoute("/simulation")({
  head: () => ({
    meta: [
      { title: "Simulation Center — QuantumShield AI" },
      { name: "description", content: "Run the end-to-end demo: traffic, AI detection, quantum-safe security, self-healing, final status." },
      { property: "og:title", content: "Simulation Center — QuantumShield AI" },
      { property: "og:description", content: "Interactive end-to-end workflow demonstration." },
    ],
  }),
  component: SimulationPage,
});

export const levelClass: Record<LogLevel, string> = {
  DEBUG: "text-muted-foreground",
  INFO: "text-info",
  SUCCESS: "text-success",
  WARN: "text-warning",
  ERROR: "text-destructive",
};

function SimulationPage() {
  const { status, config, setConfig, results, logs, progress } = useSimulation();
  const { isMock } = useLiveFeed();
  const running = status === "running";
  const consoleRef = useRef<HTMLDivElement>(null);
  const final = results.final;

  useEffect(() => {
    consoleRef.current?.scrollTo({ top: consoleRef.current.scrollHeight, behavior: "smooth" });
  }, [logs.length]);

  return (
    <>
      <PageHeader
        eyebrow="Module 07"
        title="Simulation Center"
        description={
          isMock
            ? "A frontend-only walkthrough of the intended workflow. Every result here is generated demo data, not a real security assessment."
            : "Injects synthetic attack traffic into simulated fleet nodes and runs it through real QRNG entropy, BB84 simulation, ML-KEM-768 key exchange, ML-DSA-65 digital signatures, and autonomous self-healing."
        }
        actions={<RunSimulationButton size="lg" />}
      />

      <GlassPanel className="mb-6" title="Workflow" icon={<FlaskConical />} actions={<DemoBadge label="Simulated" always />}>
        <SimulationPipeline />
      </GlassPanel>

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="relative">
          <ShineBorder
            className="w-full rounded-2xl"
            color={running ? ["#f59e0b", "#d97706"] : ["#14b8a6", "#06b6d4"]}
            borderWidth={1.5}
            duration={12}
          >
            <GlassPanel title="Scenario Injector" icon={<Settings2 />} bodyClassName="space-y-6">
              <div>
                <p className="mb-2 text-xs text-muted-foreground">Adversary scenario</p>
                <Select value={config.scenario} onValueChange={(v) => setConfig({ scenario: v as SimulationScenario })} disabled={running}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(Object.keys(scenarioLabels) as SimulationScenario[]).map((k) => (
                      <SelectItem key={k} value={k}>{scenarioLabels[k]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <div className="mb-2 flex justify-between text-xs">
                  <span className="text-muted-foreground">Attack intensity</span>
                  <span className="font-mono text-primary">{config.intensity}%</span>
                </div>
                <Slider value={[config.intensity]} min={10} max={100} step={5} disabled={running} onValueChange={([v]) => setConfig({ intensity: v ?? 60 })} />
              </div>
              <div>
                <div className="mb-2 flex justify-between text-xs">
                  <span className="text-muted-foreground">Simulated fleet nodes</span>
                  <span className="font-mono text-primary">{config.nodes}</span>
                </div>
                <Slider value={[config.nodes]} min={4} max={64} step={1} disabled={running} onValueChange={([v]) => setConfig({ nodes: v ?? 14 })} />
              </div>
              <div className="rounded-lg border border-border bg-surface/50 p-3">
                <div className="mb-2 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Execution Progress</span>
                  <span className="font-mono text-foreground font-semibold">{progress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <motion.div className="h-full bg-gradient-primary" animate={{ width: `${progress}%` }} transition={{ duration: 0.5 }} />
                </div>
                <p className="mt-3 text-[11px] text-muted-foreground">
                  In live mode each step executes against the active <span className="font-mono text-accent">POST /api/simulation/&lt;stage&gt;</span> defense backend.
                </p>
              </div>
            </GlassPanel>
          </ShineBorder>
        </div>

        <div className="min-w-0 space-y-6">
          <div className="grid gap-6 lg:grid-cols-2 [&>*]:min-w-0">
            <GlassPanel title="Stage Results" icon={<FileCheck2 />} bodyClassName="space-y-3 max-h-[420px] overflow-auto scrollbar-thin">
              {SIMULATION_STAGES.filter((s) => results[s.id]).length === 0 && (
                <div className="p-6 text-center text-sm text-muted-foreground">
                  <ShieldCheck className="mx-auto mb-2 size-8 text-primary/40" />
                  <p>Run the simulation to inspect stage telemetry & cryptographic evidence.</p>
                </div>
              )}
              <AnimatePresence>
                {SIMULATION_STAGES.map((s) => {
                  const r = results[s.id];
                  if (!r) return null;
                  return (
                    <motion.div key={s.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg border border-border bg-surface/50 p-3">
                      <div className="flex items-center justify-between">
                        <p className="font-mono text-[10px] uppercase tracking-widest text-primary">{s.label}</p>
                        <span className="font-mono text-[9px] uppercase tracking-wider text-success border border-success/30 rounded px-1.5 py-0.5 bg-success/5">
                          ATTESTED
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-foreground">{r.headline}</p>
                      <div className="mt-2 grid grid-cols-3 gap-2">
                        {r.metrics.map((m) => (
                          <div key={m.label} className="rounded border border-border bg-background/40 px-2 py-1.5">
                            <p className="text-[10px] text-muted-foreground">{m.label}</p>
                            <p className="font-mono text-xs text-foreground">{m.value}</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </GlassPanel>

            <GlassPanel title="Execution Console" icon={<TerminalSquare />} bodyClassName="p-0">
              <div ref={consoleRef} className="h-[420px] overflow-auto bg-background/50 p-4 font-mono text-xs leading-relaxed scrollbar-thin">
                <p className="text-muted-foreground">$ quantumshield simulate --scenario {config.scenario} --intensity {config.intensity} --demo</p>
                {logs.map((l) => (
                  <motion.p key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <span className="text-muted-foreground">{fmtTime(l.timestamp)}</span>{" "}
                    <span className={cn("inline-block w-16", levelClass[l.level])}>[{l.level}]</span>{" "}
                    <span className="text-accent">{l.module}</span> <span className="text-foreground">{l.message}</span>
                  </motion.p>
                ))}
                {running && <span className="inline-block h-3.5 w-2 animate-blink bg-primary align-middle" />}
              </div>
            </GlassPanel>
          </div>

          <AnimatePresence>
            {final && (
              <ShineBorder
                className="w-full rounded-2xl"
                color={["#10b981", "#14b8a6", "#06b6d4"]}
                borderWidth={2}
                duration={10}
              >
                <motion.div
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="glass hud-corners glow rounded-xl p-6"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <StatusBadge tone="success" pulse>Defense Attestation Complete</StatusBadge>
                      <DemoBadge label="Verified Result" always />
                    </div>
                    <span className="font-mono text-xs text-primary font-semibold border border-primary/30 px-2 py-0.5 rounded bg-primary/10">
                      NIST L3 CERTIFIED
                    </span>
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold text-foreground">{final.headline}</h2>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    {final.metrics.map((m) => (
                      <div key={m.label} className="rounded-lg border border-border-strong bg-primary/5 p-4">
                        <p className="text-xs text-muted-foreground">{m.label}</p>
                        <p className="mt-1 font-display text-2xl font-semibold text-primary">{m.value}</p>
                      </div>
                    ))}
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">
                    {isMock
                      ? "This report is generated from sample data to demonstrate the interface. It does not reflect any real network."
                      : "The attacks were injected into simulated nodes. The cryptography, ML-DSA signatures and containment decisions in this report come from the real backend defense engine."}
                  </p>
                </motion.div>
              </ShineBorder>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}
