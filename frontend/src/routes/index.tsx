import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, ArrowRight, HeartPulse, KeyRound, Lock, RefreshCw, Shield, ShieldCheck, Share2, Workflow } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisProps, chartColors, HudTooltip } from "@/components/charts/chart-theme";
import { DefensePerimeterRadar } from "@/components/defense/DefensePerimeterRadar";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { HudRing } from "@/components/hud/HudRing";
import { StatCard } from "@/components/hud/StatCard";
import { severityTone, StatusBadge } from "@/components/hud/StatusBadge";
import { NetworkGraph, NetworkLegend } from "@/components/network/NetworkGraph";
import { RunSimulationButton } from "@/components/simulation/RunSimulationButton";
import { SimulationPipeline } from "@/components/simulation/SimulationPipeline";
import { Button } from "@/components/ui/button";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { fmtTime, formatDuration } from "@/lib/format";
import { overviewQuery, topologyQuery } from "@/services/queries";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — QuantumShield AI" },
      { name: "description", content: "Security posture, threat activity, PQC coverage and network health at a glance (demo data)." },
      { property: "og:title", content: "Overview — QuantumShield AI" },
      { property: "og:description", content: "AI-driven post-quantum cybersecurity command dashboard." },
    ],
  }),
  loader: ({ context }) =>
    Promise.all([
      context.queryClient.ensureQueryData(overviewQuery),
      context.queryClient.ensureQueryData(topologyQuery),
    ]),
  component: Overview,
});

const kpiIcons = [Shield, Activity, KeyRound, HeartPulse];

function Overview() {
  const { data } = useSuspenseQuery(overviewQuery);
  const { data: topology } = useSuspenseQuery(topologyQuery);
  const { isMock } = useLiveFeed();

  return (
    <div className="space-y-6">
      {/* Hero command panel */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass hud-corners relative overflow-hidden rounded-2xl"
      >
        <div className="pointer-events-none absolute -right-24 -top-24 size-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 left-1/3 size-96 rounded-full bg-accent/10 blur-3xl" />
        <div className="relative grid items-center gap-8 p-6 md:p-10 lg:grid-cols-[1fr_auto]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-primary">Command Overview</span>
              <DemoBadge />
            </div>
            <h1 className="mt-4 text-4xl font-bold leading-[1.05] text-foreground md:text-5xl xl:text-6xl">
              Post-quantum defence,
              <br />
              <span className="text-gradient">self-healing by design.</span>
            </h1>
            <p className="mt-4 max-w-xl text-sm text-muted-foreground md:text-base">
              QuantumShield AI predicts threats, enforces quantum-safe cryptography and repairs the network
              automatically. Run the end-to-end demo to walk through the full workflow.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <RunSimulationButton size="xl" />
              <Button variant="hud" size="xl" asChild>
                <Link to="/simulation">
                  Simulation Center <ArrowRight />
                </Link>
              </Button>
            </div>
          </div>
          <div className="mx-auto flex justify-center">
            <DefensePerimeterRadar
              postureScore={data.postureScore}
              isolatedCount={Number(data.kpis.find((k) => k.id === "health")?.hint?.match(/(\d+)\s+isolated/)?.[1] ?? 0)}
              totalNodes={14}
            >
              <HudRing
                value={data.postureScore}
                label="Security posture"
                size={260}
                sublabel={
                  data.postureScore >= 80 ? (
                    <StatusBadge tone="success" pulse>Protected</StatusBadge>
                  ) : data.postureScore >= 60 ? (
                    <StatusBadge tone="warning" pulse>At risk</StatusBadge>
                  ) : (
                    <StatusBadge tone="danger" pulse>Under attack</StatusBadge>
                  )
                }
              />
            </DefensePerimeterRadar>
          </div>
        </div>
      </motion.section>

      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {data.kpis.map((k, i) => {
          const Icon = kpiIcons[i % kpiIcons.length] ?? Shield;
          return (
            <StatCard
              key={k.id}
              index={i}
              label={k.label}
              value={k.id === "mttr" ? formatDuration(k.value) : k.value}
              delta={k.delta}
              trend={k.trend}
              tone={k.tone}
              hint={k.hint}
              icon={<Icon />}
            />
          );
        })}
      </div>

      {/* Workflow */}
      <GlassPanel
        title="End-to-End Workflow"
        subtitle="Network Traffic → AI Threat Detection → Quantum-Safe Security → Self-Healing → Final Status"
        icon={<Workflow />}
        actions={<DemoBadge label="Simulated" />}
      >
        <SimulationPipeline />
      </GlassPanel>

      <div className="grid gap-6 xl:grid-cols-5">
        <GlassPanel
          className="xl:col-span-3"
          title={isMock ? "Network Traffic (24h)" : "Pipeline Activity"}
          subtitle={isMock ? "Inbound / outbound Mbps with anomaly count" : "Per minute: nodes scored, secure channels built, threats flagged"}
          icon={<Activity />}
          actions={<DemoBadge />}
        >
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.traffic} margin={{ left: -16, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="g-in" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={chartColors.primary} stopOpacity={0.45} />
                    <stop offset="100%" stopColor={chartColors.primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="g-out" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={chartColors.accent} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={chartColors.accent} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="time" {...axisProps} interval={3} />
                <YAxis {...axisProps} />
                <Tooltip content={<HudTooltip />} />
                <Area type="monotone" dataKey="inbound" name={isMock ? "Inbound" : "Nodes scored"} stroke={chartColors.primary} fill="url(#g-in)" strokeWidth={2} />
                <Area type="monotone" dataKey="outbound" name={isMock ? "Outbound" : "Secure channels"} stroke={chartColors.accent} fill="url(#g-out)" strokeWidth={2} />
                <Area type="monotone" dataKey="anomalies" name={isMock ? "Anomalies" : "Threats flagged"} stroke={chartColors.danger} fill="none" strokeWidth={1.5} strokeDasharray="4 3" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        <GlassPanel
          className="xl:col-span-2"
          title="Live Topology"
          subtitle={`${topology.nodes.length} nodes`}
          icon={<Share2 />}
          actions={
            <Button variant="link" size="sm" asChild>
              <Link to="/topology">Expand</Link>
            </Button>
          }
        >
          <div className="aspect-[5/3]">
            <NetworkGraph topology={topology} showLabels={false} />
          </div>
          <div className="mt-3">
            <NetworkLegend />
          </div>
        </GlassPanel>
      </div>

      <GlassPanel
        title="Recent Threat Events"
        subtitle="Latest classifications from the AI engine"
        icon={<AlertTriangle />}
        actions={
          <Button variant="link" size="sm" asChild>
            <Link to="/threats">View all</Link>
          </Button>
        }
        bodyClassName="p-0"
      >
        <ul className="divide-y divide-border">
          {data.recentThreats.map((t, i) => (
            <motion.li
              key={t.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3 text-sm hover:bg-primary/5"
            >
              <span className="w-20 font-mono text-xs text-muted-foreground">{fmtTime(t.timestamp)}</span>
              <StatusBadge tone={severityTone[t.severity]}>{t.severity}</StatusBadge>
              <span className="flex-1 font-medium text-foreground">{t.category}</span>
              <span className="font-mono text-xs text-muted-foreground">
                {t.source} → {t.target}
              </span>
              <span className="w-16 text-right font-mono text-xs text-primary">{Math.round(t.confidence * 100)}%</span>
            </motion.li>
          ))}
        </ul>
      </GlassPanel>
    </div>
  );
}
