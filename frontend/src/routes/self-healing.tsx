import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { HeartPulse, ListChecks, Network, Timer, Wrench, Zap } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisProps, chartColors, HudTooltip } from "@/components/charts/chart-theme";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { StatCard } from "@/components/hud/StatCard";
import { StatusBadge, type BadgeTone } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { NetworkGraph, NetworkLegend } from "@/components/network/NetworkGraph";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { fmtTime } from "@/lib/format";
import { USE_MOCK_DATA } from "@/services/api/config";
import { healingQuery, topologyQuery } from "@/services/queries";
import type { HealingIncident, NetworkEdge, NodeStatus, Topology } from "@/types/quantumshield";

export const Route = createFileRoute("/self-healing")({
  head: () => ({
    meta: [
      { title: "Self-Healing Network — QuantumShield AI" },
      { name: "description", content: "Automated isolation, rerouting and recovery of network faults (demo data)." },
      { property: "og:title", content: "Self-Healing Network — QuantumShield AI" },
      { property: "og:description", content: "Autonomous remediation timeline and policies." },
    ],
  }),
  loader: ({ context }) =>
    Promise.all([
      context.queryClient.ensureQueryData(healingQuery),
      context.queryClient.ensureQueryData(topologyQuery),
    ]),
  component: HealingPage,
});

const incidentTone: Record<HealingIncident["status"], BadgeTone> = {
  resolved: "success",
  "in-progress": "accent",
  escalated: "warning",
};

type Phase = "idle" | "detected" | "isolating" | "healing" | "restored";
const phaseText: Record<Phase, string> = {
  idle: "All nodes stable. Inject a demo fault to watch the recovery sequence.",
  detected: "Fault detected on Access Switch A — integrity check failed.",
  isolating: "Isolating node and rerouting traffic through Core Router 2.",
  healing: "Restoring signed configuration and re-establishing PQC tunnels.",
  restored: "Node restored. Traffic returned to primary path.",
};
const FAULT_NODE = "sw-a";

function HealingPage() {
  const { data } = useSuspenseQuery(healingQuery);
  const { data: baseTopology } = useSuspenseQuery(topologyQuery);
  const [policies, setPolicies] = useState(data.policies);
  const [phase, setPhase] = useState<Phase>("idle");
  const [incidents, setIncidents] = useState(data.incidents);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  // Live mode: follow the backend whenever it sends new data (the demo fault injector below only runs on demo data).
  useEffect(() => {
    if (USE_MOCK_DATA) return;
    setPolicies(data.policies);
    setIncidents(data.incidents);
  }, [data.policies, data.incidents]);

  const topology: Topology = useMemo(() => {
    const statusFor: Partial<Record<Phase, NodeStatus>> = {
      detected: "compromised",
      isolating: "isolated",
      healing: "healing",
      restored: "healthy",
    };
    const s = statusFor[phase];
    if (!s) return baseTopology;
    return {
      nodes: baseTopology.nodes.map((n) => (n.id === FAULT_NODE ? { ...n, status: s } : n)),
      edges: baseTopology.edges.map((e): NetworkEdge => {
        const touches = e.from === FAULT_NODE || e.to === FAULT_NODE;
        if (touches && (phase === "detected" || phase === "isolating")) return { ...e, status: "down" };
        if (phase === "isolating" && e.from === "core-2") return { ...e, status: "rerouted" };
        if (touches && phase === "healing") return { ...e, status: "rerouted" };
        return e;
      }),
    };
  }, [phase, baseTopology]);

  const injectFault = () => {
    timers.current.forEach(clearTimeout);
    setPhase("detected");
    const seq: [Phase, number][] = [["isolating", 1600], ["healing", 3400], ["restored", 5200]];
    timers.current = seq.map(([p, ms]) =>
      setTimeout(() => {
        setPhase(p);
        if (p === "restored") {
          setIncidents((list) => [
            {
              id: `HEAL-DEMO-${list.length + 1}`,
              timestamp: new Date().toISOString(),
              node: FAULT_NODE,
              issue: "Injected demo fault (integrity failure)",
              action: "Isolated, rerouted via core-2, restored signed config",
              durationSec: 5,
              status: "resolved",
            },
            ...list,
          ]);
        }
      }, ms),
    );
  };

  const busy = phase !== "idle" && phase !== "restored";

  return (
    <>
      <PageHeader
        eyebrow="Module 04"
        title="Self-Healing Network"
        description={USE_MOCK_DATA ? "Autonomous detection, isolation and recovery. The fault-injection demo below runs entirely in the browser." : "Autonomous isolation and recovery decided by Stage 3, with every command ML-DSA signed and verified."}
        actions={
          USE_MOCK_DATA ? (
            <Button variant="danger" onClick={injectFault} disabled={busy}>
              <Zap /> Inject demo fault
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard index={0} label="Mean time to heal" value={data.mttrSeconds > 0 || USE_MOCK_DATA ? `${data.mttrSeconds}s` : "—"} {...(USE_MOCK_DATA ? { delta: "-29s / wk", trend: "down" as const } : {})} tone="primary" icon={<Timer />} />
        <StatCard index={1} label="Auto-remediation" value={`${data.autoRemediationRate}%`} {...(USE_MOCK_DATA ? { delta: "+4%", trend: "up" as const } : {})} tone="success" icon={<Wrench />} />
        <StatCard index={2} label={USE_MOCK_DATA ? "Incidents (7d)" : "Incidents logged"} value={USE_MOCK_DATA ? "66" : String(data.incidents.length)} {...(USE_MOCK_DATA ? { delta: "-12%", trend: "down" as const } : {})} tone="warning" icon={<HeartPulse />} />
        <StatCard index={3} label="Active policies" value={`${policies.filter((p) => p.enabled).length}/${policies.length}`} tone="accent" icon={<ListChecks />} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-5">
        <GlassPanel className="xl:col-span-3" title="Recovery Visualiser" icon={<Network />} actions={<DemoBadge label="Simulated" />}>
          <div className="aspect-[5/3]">
            <NetworkGraph topology={topology} selectedId={phase !== "idle" ? FAULT_NODE : null} />
          </div>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <AnimatePresence mode="wait">
              <motion.p
                key={phase}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                className="font-mono text-xs text-primary"
              >
                › {USE_MOCK_DATA || phase !== "idle" ? phaseText[phase] : "Live view: isolated nodes are grey, with a broken red link to the controller."}
              </motion.p>
            </AnimatePresence>
            <NetworkLegend />
          </div>
        </GlassPanel>

        <GlassPanel className="xl:col-span-2" title="Healing Policies" icon={<ListChecks />} bodyClassName="space-y-3">
          {policies.map((p) => (
            <div key={p.id} className="rounded-lg border border-border bg-surface/50 p-3">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-foreground">{p.name}</p>
                <Switch
                  checked={p.enabled}
                  onCheckedChange={(v) => setPolicies((list) => list.map((x) => (x.id === p.id ? { ...x, enabled: v } : x)))}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                <span className="text-accent">When</span> {p.trigger} <span className="text-accent">→</span> {p.action}
              </p>
            </div>
          ))}
        </GlassPanel>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <GlassPanel title="MTTR Trend" subtitle="Seconds to recovery vs incidents" icon={<Timer />} actions={<DemoBadge />}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.mttrTrend} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="day" {...axisProps} />
                <YAxis {...axisProps} />
                <Tooltip content={<HudTooltip />} cursor={{ fill: "var(--color-primary)", fillOpacity: 0.06 }} />
                <Bar dataKey="incidents" name="Incidents" fill={chartColors.accent} fillOpacity={0.5} radius={[4, 4, 0, 0]} />
                <Line type="monotone" dataKey="mttr" name="MTTR (s)" stroke={chartColors.primary} strokeWidth={2} dot={{ r: 3, fill: chartColors.primary }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        <GlassPanel title="Remediation Timeline" icon={<HeartPulse />} actions={<DemoBadge />} bodyClassName="max-h-[340px] overflow-auto scrollbar-thin">
          <ol className="relative space-y-5 border-l border-border-strong pl-5">
            <AnimatePresence initial={false}>
              {incidents.map((inc) => (
                <motion.li key={inc.id} layout initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="relative">
                  <span className="absolute -left-[25px] top-1.5 size-2.5 rounded-full border border-accent bg-background" />
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs text-primary">{inc.id}</span>
                    <StatusBadge tone={incidentTone[inc.status]}>{inc.status}</StatusBadge>
                    <span className="ml-auto font-mono text-[11px] text-muted-foreground">{fmtTime(inc.timestamp)} · {inc.durationSec}s</span>
                  </div>
                  <p className="mt-1 text-sm text-foreground">{inc.issue} <span className="text-muted-foreground">on {inc.node}</span></p>
                  <p className="text-xs text-muted-foreground">↳ {inc.action}</p>
                </motion.li>
              ))}
            </AnimatePresence>
          </ol>
        </GlassPanel>
      </div>
    </>
  );
}
