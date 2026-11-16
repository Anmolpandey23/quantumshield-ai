import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, Gauge, Pause, Play, Workflow } from "lucide-react";
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
import { cn } from "@/lib/utils";
import { USE_MOCK_DATA } from "@/services/api/config";
import { pipelineQuery } from "@/services/queries";
import type { PipelineStage, PipelineStageStatus } from "@/types/quantumshield";

export const Route = createFileRoute("/pipeline")({
  head: () => ({
    meta: [
      { title: "Pipeline Monitor — QuantumShield AI" },
      { name: "description", content: "Throughput, latency and queue depth for each processing stage (demo data)." },
      { property: "og:title", content: "Pipeline Monitor — QuantumShield AI" },
      { property: "og:description", content: "Processing pipeline health and throughput." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(pipelineQuery),
  component: PipelinePage,
});

const stageTone: Record<PipelineStageStatus, BadgeTone> = {
  running: "success",
  idle: "muted",
  degraded: "warning",
  error: "danger",
};
const lineColors = [chartColors.primary, chartColors.accent, chartColors.warning, chartColors.info];

function PipelinePage() {
  const { data } = useSuspenseQuery(pipelineQuery);
  const [stages, setStages] = useState<PipelineStage[]>(data.stages);
  const [live, setLive] = useState(true);
  // Demo mode jitters local copies; live mode always shows what the backend just sent.
  const shown = USE_MOCK_DATA ? stages : data.stages;

  // Client-side jitter so the preview feels live (demo only).
  useEffect(() => {
    if (!live || !USE_MOCK_DATA) return;
    const t = setInterval(() => {
      setStages((list) =>
        list.map((s) =>
          s.status === "idle"
            ? s
            : {
                ...s,
                throughput: Math.max(50, Math.round(s.throughput * (0.97 + Math.random() * 0.06))),
                queue: Math.max(0, Math.round(s.queue * (0.9 + Math.random() * 0.2))),
              },
        ),
      );
    }, 1800);
    return () => clearInterval(t);
  }, [live]);

  return (
    <>
      <PageHeader
        eyebrow="Module 06"
        title="Pipeline Monitor"
        description={USE_MOCK_DATA ? "Each stage maps to one of your Python modules. Numbers drift slightly to preview live updates." : "Each stage maps to one Python module. Rates are real event counts; n/a means the pipeline does not measure it."}
        actions={
          USE_MOCK_DATA ? (
            <Button variant="hud" onClick={() => setLive((v) => !v)}>
              {live ? <Pause /> : <Play />} {live ? "Pause live feed" : "Resume live feed"}
            </Button>
          ) : null
        }
      />

      <GlassPanel title="Processing Flow" icon={<Workflow />} actions={<DemoBadge />}>
        <div className="flex flex-col gap-1 xl:flex-row xl:items-center">
          {shown.map((s, i) => (
            <Fragment key={s.id}>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className={cn(
                  "w-full min-w-0 flex-1 self-stretch rounded-lg border bg-surface/50 p-4",
                  s.status === "degraded" ? "border-warning/40" : "border-border",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">0{i + 1}</span>
                  <StatusBadge tone={stageTone[s.status]} pulse={s.status !== "idle"} className="px-1.5">{s.status}</StatusBadge>
                </div>
                <p className="mt-2 font-display text-sm font-semibold text-foreground">{s.name}</p>
                <p className="truncate font-mono text-[11px] text-accent" title={s.module}>{s.module}</p>
                <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-[11px]">
                  <div><p className="text-muted-foreground">ev/s</p><p className="text-foreground tabular-nums">{s.throughput.toLocaleString("en-US")}</p></div>
                  <div><p className="text-muted-foreground">p50</p><p className="text-foreground">{s.latencyMs == null ? "n/a" : `${s.latencyMs} ms`}</p></div>
                </div>
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

      <div className="mt-6 grid gap-6 xl:grid-cols-5">
        <GlassPanel className="xl:col-span-3" title="Throughput History" subtitle={USE_MOCK_DATA ? "Events/sec, last 20 minutes" : "Events/sec (per-minute average), last 20 active minutes"} icon={<Activity />} actions={<DemoBadge />}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.throughputHistory} margin={{ left: -4, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="time" {...axisProps} interval={3} />
                <YAxis {...axisProps} />
                <Tooltip content={<HudTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {data.stages.slice(0, 4).map((s, i) => (
                  <Line key={s.id} type="monotone" dataKey={s.id} name={s.name} stroke={lineColors[i]} strokeWidth={2} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        <GlassPanel className="xl:col-span-2" title="Stage Health" icon={<Gauge />} bodyClassName="space-y-4">
          {shown.map((s) => (
            <div key={s.id}>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="text-foreground">{s.name}</span>
                <span className="font-mono text-muted-foreground">queue {s.queue.toLocaleString("en-US")}{s.uptime == null ? "" : ` · ${s.uptime}% up`}</span>
              </div>
              <Meter value={Math.min(100, (s.queue / 2000) * 100)} tone={s.queue > 1500 ? "warning" : "accent"} />
            </div>
          ))}
          <p className="text-[11px] text-muted-foreground">Bar shows queue depth against a 2,000-event soft limit.</p>
        </GlassPanel>
      </div>
    </>
  );
}
