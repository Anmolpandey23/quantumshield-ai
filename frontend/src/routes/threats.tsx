import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { BrainCircuit, Crosshair, Gauge, Radar as RadarIcon, Search, ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { axisProps, chartColors, HudTooltip } from "@/components/charts/chart-theme";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { HudRing } from "@/components/hud/HudRing";
import { Meter } from "@/components/hud/Meter";
import { severityTone, StatusBadge, type BadgeTone } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { ShineBorder } from "@/components/ui/shine-border";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { fmtDateTime } from "@/lib/format";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { threatsQuery } from "@/services/queries";
import type { Severity, ThreatEvent } from "@/types/quantumshield";

export const Route = createFileRoute("/threats")({
  head: () => ({
    meta: [
      { title: "AI Threat Prediction — QuantumShield AI" },
      { name: "description", content: "Predicted vs observed risk, threat categories and AI classifications (demo data)." },
      { property: "og:title", content: "AI Threat Prediction — QuantumShield AI" },
      { property: "og:description", content: "AI model insights and threat event stream." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(threatsQuery),
  component: ThreatsPage,
});

const statusTone: Record<ThreatEvent["status"], BadgeTone> = {
  blocked: "success",
  mitigated: "accent",
  monitoring: "info",
  investigating: "warning",
};

function ThreatsPage() {
  const { data } = useSuspenseQuery(threatsQuery);
  const { isMock } = useLiveFeed();
  const [threshold, setThreshold] = useState(80);
  const [severities, setSeverities] = useState<Severity[]>(["critical", "high", "medium", "low"]);
  const [query, setQuery] = useState("");

  const filtered = useMemo(
    () =>
      data.events.filter(
        (e) =>
          e.confidence * 100 >= threshold &&
          severities.includes(e.severity) &&
          (query === "" ||
            `${e.category} ${e.source} ${e.target} ${e.id}`.toLowerCase().includes(query.toLowerCase())),
      ),
    [data.events, threshold, severities, query],
  );

  const m = data.model;
  const metricRows: (readonly [string, number | null | undefined, "primary" | "accent" | "success"])[] = [
    ["Accuracy", m.accuracy, "primary"],
    ["Precision", m.precision, "accent"],
    ["Recall", m.recall, "success"],
    ...(m.macroF1 != null ? [["Macro-F1", m.macroF1, "primary"] as const] : []),
  ];

  return (
    <>
      <PageHeader
        eyebrow="Module 02"
        title="AI Threat Prediction"
        description={isMock ? "Forecasted risk and classified threat events produced by the AI engine. Connect your Python model to replace this sample output." : "Threat events classified by the Stage 1 models, with the risk each node carries right now."}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <ShineBorder
          borderRadius={16}
          color={data.currentRisk >= 70 ? ["#ef4444", "#f97316", "#dc2626"] : ["#14b8a6", "#38bdf8", "#06b6d4"]}
          className="size-full"
        >
          <GlassPanel title="Current Risk Index" icon={<Gauge />} actions={<DemoBadge />} className="border-0 bg-transparent">
            <div className="flex flex-col items-center">
              <HudRing value={data.currentRisk} label="Risk / 100" size={200} sublabel={<StatusBadge tone={data.currentRisk >= 70 ? "danger" : data.currentRisk >= 40 ? "warning" : "success"} pulse>{data.currentRisk >= 70 ? "High" : data.currentRisk >= 40 ? "Elevated" : "Low"}</StatusBadge>} />
              <p className="mt-3 text-center text-xs text-muted-foreground">{isMock ? "Next-hour forecast based on sample trend." : "Highest node risk score reported by Stage 1 right now."}</p>
            </div>
          </GlassPanel>
        </ShineBorder>

        <ShineBorder
          borderRadius={16}
          color={["#14b8a6", "#a855f7", "#38bdf8"]}
          className="lg:col-span-2 size-full"
        >
          <GlassPanel title="Model" subtitle={m.architecture} icon={<BrainCircuit />} className="border-0 bg-transparent">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-3">
              <Row label="Name" value={m.name} />
              <Row label="Version" value={m.version} />
              <Row label="Last trained" value={m.lastTrained ? `${fmtDateTime(m.lastTrained)} UTC` : "not trained yet"} />
            </div>
            <div className="space-y-4">
              {metricRows.map(([label, v, tone]) => (
                <div key={label}>
                  <div className="mb-1.5 flex justify-between text-xs">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="font-mono text-foreground">{v == null ? "n/a" : `${(v * 100).toFixed(1)}%`}</span>
                  </div>
                  <Meter value={(v ?? 0) * 100} tone={tone} />
                </div>
              ))}
              <p className="text-[11px] text-muted-foreground">{isMock ? "Metrics are placeholders until your model reports them." : "n/a = the backend has no measurement. Nothing is estimated."}</p>
            </div>
          </div>
        </GlassPanel>
        </ShineBorder>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-5">
        <GlassPanel className="xl:col-span-3" title="Predicted vs Observed Risk" subtitle={isMock ? "Hourly, last 24h" : "Per minute, from live pipeline events"} icon={<Crosshair />} actions={<DemoBadge />}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.riskTrend} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="hour" {...axisProps} interval={3} />
                <YAxis {...axisProps} domain={[0, 100]} />
                <Tooltip content={<HudTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: chartColors.axis }} />
                <Line type="monotone" dataKey="predicted" name={isMock ? "Predicted" : "Predicted risk"} stroke={chartColors.primary} strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="observed" name={isMock ? "Observed" : "Anomaly score"} stroke={chartColors.warning} strokeWidth={2} dot={false} connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
        <GlassPanel className="xl:col-span-2" title="Threat Vectors" subtitle="Category risk scores" icon={<RadarIcon />} actions={<DemoBadge />}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={data.categories} outerRadius="72%">
                <PolarGrid stroke={chartColors.grid} />
                <PolarAngleAxis dataKey="category" tick={{ fill: chartColors.axis, fontSize: 11 }} />
                <Radar dataKey="score" name="Score" stroke={chartColors.accent} fill={chartColors.accent} fillOpacity={0.25} />
                <Tooltip content={<HudTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
      </div>

      <GlassPanel
        className="mt-6"
        title="Threat Event Stream"
        subtitle={`${filtered.length} of ${data.events.length} events match filters`}
        icon={<ShieldAlert />}
        actions={<DemoBadge />}
        bodyClassName="p-0"
      >
        <div className="grid gap-4 border-b border-border p-5 md:grid-cols-3 md:items-center">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search category, IP, node…" className="pl-9" />
          </div>
          <ToggleGroup
            type="multiple"
            value={severities}
            onValueChange={(v) => setSeverities(v as Severity[])}
            className="justify-start"
          >
            {(["critical", "high", "medium", "low"] as const).map((s) => (
              <ToggleGroupItem key={s} value={s} size="sm" className="font-mono text-[10px] uppercase data-[state=on]:bg-primary/15 data-[state=on]:text-primary">
                {s}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          <div>
            <div className="mb-2 flex justify-between text-xs">
              <span className="text-muted-foreground">Min. confidence</span>
              <span className="font-mono text-primary">{threshold}%</span>
            </div>
            <Slider value={[threshold]} min={50} max={99} step={1} onValueChange={([v]) => setThreshold(v ?? 80)} />
          </div>
        </div>
        <div className="max-h-[480px] overflow-auto scrollbar-thin">
          <table className="w-full min-w-[760px] text-sm">
            <thead className="sticky top-0 bg-surface/95 backdrop-blur">
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="px-5 py-3 font-medium">ID</th>
                <th className="px-3 py-3 font-medium">Time</th>
                <th className="px-3 py-3 font-medium">Category</th>
                <th className="px-3 py-3 font-medium">Severity</th>
                <th className="px-3 py-3 font-medium">Source → Target</th>
                <th className="px-3 py-3 font-medium">Confidence</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((e) => (
                <tr key={e.id} className="hover:bg-primary/5">
                  <td className="px-5 py-3 font-mono text-xs text-primary">{e.id}</td>
                  <td className="px-3 py-3 font-mono text-xs text-muted-foreground">{fmtDateTime(e.timestamp)}</td>
                  <td className="px-3 py-3 text-foreground">{e.category}</td>
                  <td className="px-3 py-3"><StatusBadge tone={severityTone[e.severity]}>{e.severity}</StatusBadge></td>
                  <td className="px-3 py-3 font-mono text-xs text-muted-foreground">{e.source} → {e.target}</td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <Meter value={e.confidence * 100} className="w-16" />
                      <span className="font-mono text-xs">{Math.round(e.confidence * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3"><StatusBadge tone={statusTone[e.status]}>{e.status}</StatusBadge></td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-sm text-muted-foreground">No events match these filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassPanel>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-md border border-border bg-surface/50 px-3 py-2.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="truncate font-mono text-xs text-foreground">{value}</span>
    </div>
  );
}
