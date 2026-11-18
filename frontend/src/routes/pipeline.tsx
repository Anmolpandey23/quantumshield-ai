import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, Cpu, Gauge, KeyRound, Pause, Play, ShieldAlert, ShieldCheck, Workflow, Zap } from "lucide-react";
import { Fragment, useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisProps, chartColors, HudTooltip } from "@/components/charts/chart-theme";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { FlowArrow } from "@/components/hud/FlowArrow";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { Meter } from "@/components/hud/Meter";
import { StatusBadge, type BadgeTone } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { ShineBorder } from "@/components/ui/shine-border";
import { mockPipeline } from "@/data/mock/pipeline";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { cn } from "@/lib/utils";
import { pipelineQuery } from "@/services/queries";
import type { PipelineStage, PipelineStageStatus } from "@/types/quantumshield";

export const Route = createFileRoute("/pipeline")({
  head: () => ({
    meta: [
      { title: "Pipeline Monitor — QuantumShield AI" },
      { name: "description", content: "Throughput, latency and queue depth for each processing stage." },
      { property: "og:title", content: "Pipeline Monitor — QuantumShield AI" },
      { property: "og:description", content: "Processing pipeline health and throughput." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(pipelineQuery),
  component: PipelinePage,
});

const initialDemoStages: PipelineStage[] = [
  { id: "ingest", name: "Traffic Ingestion", module: "traffic_collector.py", status: "running", throughput: 13595, latencyMs: 3, queue: 120, uptime: 99.98 },
  { id: "features", name: "Feature Extraction", module: "feature_engineering.py", status: "running", throughput: 10882, latencyMs: 7, queue: 340, uptime: 99.95 },
  { id: "inference", name: "AI Threat Inference", module: "threat_model.py", status: "degraded", throughput: 9399, latencyMs: 24, queue: 1820, uptime: 99.41 },
  { id: "pqc", name: "PQC Enforcement", module: "pqc_engine.py", status: "running", throughput: 11235, latencyMs: 5, queue: 90, uptime: 99.99 },
  { id: "healing", name: "Self-Healing Orchestrator", module: "self_healing.py", status: "running", throughput: 359, latencyMs: 38, queue: 4, uptime: 99.9 },
  { id: "report", name: "Reporting & Audit", module: "reporter.py", status: "idle", throughput: 120, latencyMs: 12, queue: 0, uptime: 100 },
];

const stageTone: Record<PipelineStageStatus, BadgeTone> = {
  running: "success",
  idle: "muted",
  degraded: "warning",
  error: "danger",
};
const lineColors = [chartColors.primary, chartColors.accent, chartColors.warning, chartColors.info];

function PipelinePage() {
  const { data } = useSuspenseQuery(pipelineQuery);
  const { isLive: live, toggle: handleToggleFeed } = useLiveFeed();
  const [selectedStage, setSelectedStage] = useState<string>("ingest");
  const [demoStages, setDemoStages] = useState<PipelineStage[]>(initialDemoStages);
  const [demoHistory, setDemoHistory] = useState(mockPipeline.throughputHistory);

  // When live feed is ON: show live backend data (data.stages).
  // When live feed is PAUSED (OFF): show demo data (demoStages) with simulated dynamic drift.
  const shown = live ? data.stages : demoStages;

  // Active client-side jitter ONLY runs when live feed is paused (Demo Data mode).
  useEffect(() => {
    if (live) return; // If live feed is active, demo data generator does NOT run.

    const t = setInterval(() => {
      setDemoStages((list) =>
        list.map((s) => {
          if (s.status === "idle") return s;
          const driftRatio = 0.96 + Math.random() * 0.08;
          return {
            ...s,
            throughput: Math.max(80, Math.round(s.throughput * driftRatio)),
            queue: Math.max(0, Math.round(s.queue * (0.88 + Math.random() * 0.24))),
            latencyMs: s.latencyMs != null ? Math.max(1, Math.round(s.latencyMs + (Math.random() * 4 - 2))) : null,
          };
        }),
      );

      // Also gently drift the demo throughput history chart
      setDemoHistory((prev) => {
        if (!prev.length) return prev;
        const last = prev[prev.length - 1];
        const updated = {
          ...last,
          ingest: Math.round(Number(last["ingest"] || 12000) * (0.97 + Math.random() * 0.06)),
          features: Math.round(Number(last["features"] || 11000) * (0.97 + Math.random() * 0.06)),
          inference: Math.round(Number(last["inference"] || 9500) * (0.97 + Math.random() * 0.06)),
          pqc: Math.round(Number(last["pqc"] || 9000) * (0.97 + Math.random() * 0.06)),
        };
        return [...prev.slice(0, -1), updated];
      });
    }, 1200);

    return () => clearInterval(t);
  }, [live]);

  const hasDegraded = shown.some((s) => s.status === "degraded" || s.status === "error");

  return (
    <>
      <PageHeader
        eyebrow="Module 06"
        title="Pipeline Monitor"
        description={
          live
            ? "Real-time cyber defense execution pipeline: sub-25ms zero-trust packet flow through AI inference, PQC encapsulation, and automated isolation."
            : "Live feed paused: showing simulated demo telemetry with dynamic jitter."
        }
        actions={
          <div className="flex items-center gap-3">
            <StatusBadge tone={live ? "success" : "warning"} pulse={live}>
              {live ? "Live pipeline active" : "Demo telemetry"}
            </StatusBadge>
            <Button
              variant="hud"
              onClick={handleToggleFeed}
              className="font-mono text-xs uppercase tracking-wider gap-2 px-4 py-2 border-primary/40 bg-surface/80 hover:bg-surface hover:border-primary transition-all shadow-[0_0_15px_rgba(20,184,166,0.15)]"
            >
              {live ? <Pause className="size-4" /> : <Play className="size-4" />}
              {live ? "PAUSE LIVE FEED" : "START LIVE FEED"}
            </Button>
          </div>
        }
      />

      <ShineBorder
        className="w-full rounded-2xl mb-6"
        color={["#14b8a6", "#06b6d4"]}
        borderWidth={1.5}
        duration={14}
      >
        <GlassPanel title="Processing Flow & Defense Handshake" icon={<Workflow />} actions={!live ? <DemoBadge /> : null}>
          <div className="flex flex-col gap-1 xl:flex-row xl:items-center">
            {shown.map((s, i) => (
              <Fragment key={s.id}>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                  onClick={() => setSelectedStage(s.id)}
                  className={cn(
                    "relative w-full min-w-0 flex-1 self-stretch rounded-lg border bg-surface/50 p-4 cursor-pointer transition-all",
                    s.status === "degraded"
                      ? "border-warning/60 shadow-[0_0_15px_rgba(245,158,11,0.25)]"
                      : selectedStage === s.id
                        ? "border-primary/60 shadow-[0_0_15px_rgba(20,184,166,0.25)]"
                        : "border-border/60 hover:border-border-strong",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] text-muted-foreground">0{i + 1}</span>
                    <StatusBadge tone={stageTone[s.status]} pulse={s.status !== "idle"} className="px-1.5">{s.status}</StatusBadge>
                  </div>
                  <p className="mt-2 font-display text-sm font-semibold text-foreground">{s.name}</p>
                  <p className="truncate font-mono text-[11px] text-accent" title={s.module}>{s.module}</p>
                  <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-[11px]">
                    <div><p className="text-muted-foreground">ev/s</p><p className="text-foreground tabular-nums font-semibold">{s.throughput.toLocaleString("en-US")}</p></div>
                    <div><p className="text-muted-foreground">p50</p><p className="text-foreground font-semibold">{s.latencyMs == null ? "n/a" : `${s.latencyMs} ms`}</p></div>
                  </div>

                  {selectedStage === s.id && (
                    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 flex items-center justify-center pointer-events-none">
                      <div className="relative flex size-6 items-center justify-center rounded-full border border-primary/50 bg-background shadow-[0_0_12px_rgba(20,184,166,0.8)]">
                        <span className="size-2 rounded-full bg-primary animate-ping" />
                        <span className="absolute size-2 rounded-full bg-primary" />
                      </div>
                    </div>
                  )}
                </motion.div>
                {i < shown.length - 1 && (
                  <FlowArrow
                    state={live ? (s.status === "degraded" ? "active" : "done") : "idle"}
                    horizontalAt="xl"
                  />
                )}
              </Fragment>
            ))}
          </div>
        </GlassPanel>
      </ShineBorder>

      <div className="grid gap-6 xl:grid-cols-5">
        <GlassPanel
          className="xl:col-span-3"
          title="Throughput Telemetry History"
          subtitle={live ? "Events/sec (per-minute average), from live defense engine" : "Events/sec, last 20 minutes (simulated demo stream)"}
          icon={<Activity />}
          actions={!live ? <DemoBadge /> : null}
        >
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={live ? data.throughputHistory : demoHistory} margin={{ left: -4, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="time" {...axisProps} interval={3} />
                <YAxis {...axisProps} />
                <Tooltip content={<HudTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {(live ? data.stages : demoStages).slice(0, 4).map((s, i) => (
                  <Line key={s.id} type="monotone" dataKey={s.id} name={s.name} stroke={lineColors[i]} strokeWidth={2} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        <GlassPanel className="xl:col-span-2" title="Stage Defense Health" icon={<Gauge />} bodyClassName="space-y-4">
          {shown.map((s) => (
            <div key={s.id}>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="text-foreground">{s.name}</span>
                <span className="font-mono text-muted-foreground">queue {s.queue.toLocaleString("en-US")}{s.uptime == null ? "" : ` · ${s.uptime}% up`}</span>
              </div>
              <Meter value={Math.min(100, (s.queue / 2000) * 100)} tone={s.queue > 1500 ? "warning" : "accent"} />
            </div>
          ))}
          <p className="text-[11px] text-muted-foreground">Queue depth reflects real-time packet buffering against a 2,000-event soft limit.</p>
        </GlassPanel>
      </div>
    </>
  );
}
