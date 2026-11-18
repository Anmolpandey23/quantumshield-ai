import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Clock4, Cpu, KeyRound, Link2, Lock, RefreshCw, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisProps, chartColors, HudTooltip } from "@/components/charts/chart-theme";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { HudRing } from "@/components/hud/HudRing";
import { Meter } from "@/components/hud/Meter";
import { StatusBadge, type BadgeTone } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { ShineBorder } from "@/components/ui/shine-border";
import { Switch } from "@/components/ui/switch";
import { fmtDateTime, fmtTime } from "@/lib/format";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { cryptoQuery } from "@/services/queries";
import type { CryptoSession, PqcAlgorithm } from "@/types/quantumshield";

export const Route = createFileRoute("/cryptography")({
  head: () => ({
    meta: [
      { title: "Quantum Cryptography — QuantumShield AI" },
      { name: "description", content: "Post-quantum algorithms, sessions, key rotation and benchmarks (demo data)." },
      { property: "og:title", content: "Quantum Cryptography — QuantumShield AI" },
      { property: "og:description", content: "ML-KEM and ML-DSA post-quantum security status." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(cryptoQuery),
  component: CryptoPage,
});

const algoTone: Record<PqcAlgorithm["status"], BadgeTone> = { active: "success", standby: "info", testing: "warning" };
const modeTone: Record<CryptoSession["mode"], BadgeTone> = { hybrid: "accent", "pqc-only": "success", classical: "warning" };

function randomHex(bytes: number) {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

function DemoKeyGenerator() {
  const [hex, setHex] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  const generate = () => {
    setBusy(true);
    let n = 0;
    timer.current = setInterval(() => {
      setHex(randomHex(48));
      if (++n > 14 && timer.current) {
        clearInterval(timer.current);
        setBusy(false);
      }
    }, 70);
  };

  return (
    <div>
      <div className="relative min-h-28 overflow-hidden rounded-lg border border-border bg-background/60 p-4 font-mono text-xs leading-relaxed break-all text-primary/90">
        {hex ?? <span className="text-muted-foreground">Press generate to preview the key-exchange animation.</span>}
        {busy && <span className="absolute inset-x-0 top-0 h-1/2 animate-scan bg-gradient-to-b from-transparent via-primary/10 to-transparent" />}
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[11px] text-muted-foreground">Random bytes for visual demo only — not a real ML-KEM key.</p>
        <Button variant="hud" size="sm" onClick={generate} disabled={busy}>
          {busy ? <RefreshCw className="animate-spin" /> : <Sparkles />}
          Generate demo keypair
        </Button>
      </div>
    </div>
  );
}

function CryptoPage() {
  const { data } = useSuspenseQuery(cryptoQuery);
  const { isMock } = useLiveFeed();
  const [hybrid, setHybrid] = useState(true);
  const [autoRotate, setAutoRotate] = useState(true);

  return (
    <>
      <PageHeader
        eyebrow="Module 03"
        title="Quantum Cryptography"
        description="NIST post-quantum algorithms protecting tunnels and signatures. Swap in your PQC module's status via the service layer."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassPanel title="PQC Coverage" icon={<Lock />} actions={<DemoBadge />}>
          <div className="flex flex-col items-center">
            <HudRing value={data.coverage} label={isMock ? "% links quantum-safe" : "% nodes holding a quantum-safe key"} size={200} />
            <div className="mt-5 w-full space-y-3">
              <ToggleRow label="Hybrid mode (classical + PQC)" checked={hybrid} onChange={setHybrid} />
              <ToggleRow label="Automatic key rotation" checked={autoRotate} onChange={setAutoRotate} />
              <p className="text-[11px] text-muted-foreground">Controls are UI-only in this preview.</p>
            </div>
          </div>
        </GlassPanel>

        <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2">
          {data.algorithms.map((a, i) => (
            <ShineBorder
              key={a.id}
              borderRadius={16}
              color={a.id === "mlkem" ? ["#14b8a6", "#38bdf8", "#06b6d4"] : ["#a855f7", "#ec4899", "#8b5cf6"]}
              className="size-full"
            >
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="size-full p-5"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{a.role}</p>
                    <h3 className="mt-1 text-xl font-semibold text-foreground">{a.name}</h3>
                    <p className="text-xs text-muted-foreground">{a.family} · {a.standard}</p>
                  </div>
                  <StatusBadge tone={algoTone[a.status]} pulse={a.status === "active"}>{a.status}</StatusBadge>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-md border border-border bg-surface/50 p-2">
                    <p className="text-muted-foreground">NIST level</p>
                    <p className="font-mono text-foreground font-bold text-primary">L{a.securityLevel} (Quantum-Safe)</p>
                  </div>
                  <div className="rounded-md border border-border bg-surface/50 p-2">
                    <p className="text-muted-foreground">Public key</p>
                    <p className="font-mono text-foreground">{a.publicKeyBytes.toLocaleString("en-US")} B</p>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="mb-1.5 flex justify-between text-xs">
                    <span className="text-muted-foreground">{a.usageLabel ?? "Traffic share"}</span>
                    <span className="font-mono text-primary">{a.usage}%</span>
                  </div>
                  <Meter value={a.usage} tone="accent" />
                </div>
              </motion.div>
            </ShineBorder>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <GlassPanel title="Operation Latency" subtitle={isMock ? "Classical vs post-quantum (ms)" : "Measured Stage 2 step timings, average (ms)"} icon={<Cpu />} actions={<DemoBadge label="Illustrative" />}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.benchmarks} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="operation" {...axisProps} />
                <YAxis {...axisProps} />
                <Tooltip content={<HudTooltip />} cursor={{ fill: "var(--color-primary)", fillOpacity: 0.06 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {isMock && <Bar dataKey="classicalMs" name="Classical" fill={chartColors.info} radius={[4, 4, 0, 0]} />}
                <Bar dataKey="pqcMs" name={isMock ? "PQC" : "Measured"} fill={chartColors.primary} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
        <GlassPanel title="Key Exchange Visualiser" subtitle="ML-KEM encapsulation preview" icon={<KeyRound />} actions={<DemoBadge always />}>
          <DemoKeyGenerator />
          <div className="mt-6">
            <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Key rotation timeline</p>
            <ol className="relative space-y-4 border-l border-border-strong pl-5">
              {data.rotations.map((r) => (
                <li key={r.id} className="relative">
                  <span className="absolute -left-[25px] top-1 size-2.5 rounded-full border border-primary bg-background" />
                  <p className="text-sm text-foreground">{r.algorithm} <span className="text-muted-foreground">· {r.scope}</span></p>
                  <p className="flex items-center gap-1 font-mono text-[11px] text-muted-foreground"><Clock4 className="size-3" />{fmtDateTime(r.timestamp)} UTC</p>
                </li>
              ))}
            </ol>
          </div>
        </GlassPanel>
      </div>

      <GlassPanel className="mt-6" title="Active Secure Sessions" icon={<Link2 />} actions={<DemoBadge />} bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="px-5 py-3 font-medium">Peer</th>
                <th className="px-3 py-3 font-medium">KEM</th>
                <th className="px-3 py-3 font-medium">Signature</th>
                <th className="px-3 py-3 font-medium">Mode</th>
                <th className="px-3 py-3 font-medium">Established</th>
                <th className="px-5 py-3 text-right font-medium">Handshake</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
                {data.sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-primary/5">
                    <td className="px-5 py-3 font-mono text-xs text-foreground">{s.peer}</td>
                    <td className="px-3 py-3 font-mono text-xs text-primary">{s.kem}</td>
                    <td className="px-3 py-3 font-mono text-xs text-accent">{s.signature}</td>
                    <td className="px-3 py-3"><StatusBadge tone={modeTone[s.mode]}>{s.mode}</StatusBadge></td>
                    <td className="px-3 py-3 font-mono text-xs text-muted-foreground">{fmtTime(s.established)}</td>
                    <td className="px-5 py-3 text-right font-mono text-xs">{s.latencyMs.toFixed(1)} ms</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </GlassPanel>
    </>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface/50 px-3 py-2.5 text-xs text-foreground">
      {label}
      <Switch checked={checked} onCheckedChange={onChange} />
    </label>
  );
}
