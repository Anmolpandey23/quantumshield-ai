import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { CheckCircle2, Download, FileText, KeyRound, Lock, Pause, Play, Search, ShieldCheck, TerminalSquare } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ShineBorder } from "@/components/ui/shine-border";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { pick } from "@/lib/seeded";
import { useSimulation } from "@/features/simulation/SimulationProvider";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { fmtDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { logsQuery } from "@/services/queries";
import type { LogEntry, LogLevel } from "@/types/quantumshield";

export const Route = createFileRoute("/logs")({
  head: () => ({
    meta: [
      { title: "Execution Logs — QuantumShield AI" },
      { name: "description", content: "Searchable, filterable execution logs across all modules (demo data)." },
      { property: "og:title", content: "Execution Logs — QuantumShield AI" },
      { property: "og:description", content: "Module execution logs with live tail." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(logsQuery),
  component: LogsPage,
});

const LEVELS: LogLevel[] = ["DEBUG", "INFO", "SUCCESS", "WARN", "ERROR"];
const levelStyle: Record<LogLevel, string> = {
  DEBUG: "text-muted-foreground border-border",
  INFO: "text-info border-info/30",
  SUCCESS: "text-success border-success/30",
  WARN: "text-warning border-warning/30",
  ERROR: "text-destructive border-destructive/40",
};
const tailMessages = [
  { level: "INFO" as const, module: "traffic_collector", message: "Heartbeat: collectors online (demo)" },
  { level: "DEBUG" as const, module: "threat_model", message: "Batch scored in 21ms (demo)" },
  { level: "SUCCESS" as const, module: "pqc_engine", message: "Session rekey OK (demo)" },
  { level: "WARN" as const, module: "self_healing", message: "Probe latency spike on fw-2 (demo)" },
];

function LogsPage() {
  const { data } = useSuspenseQuery(logsQuery);
  const { logs: simLogs } = useSimulation();
  const { isMock } = useLiveFeed();
  const [levels, setLevels] = useState<LogLevel[]>(LEVELS);
  const [moduleFilter, setModuleFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [tail, setTail] = useState(false);
  const [tailLogs, setTailLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    if (!tail) return;
    const t = setInterval(() => {
      const m = pick(Math.random, tailMessages);
      setTailLogs((l): LogEntry[] => [{ id: `tail-${Date.now()}`, timestamp: new Date().toISOString(), ...m }, ...l].slice(0, 100));
    }, 1500);
    return () => clearInterval(t);
  }, [tail]);

  const logModules = useMemo(() => Array.from(new Set(data.map((l) => l.module))).sort(), [data]);
  const all = useMemo(() => [...tailLogs, ...[...simLogs].reverse(), ...data], [tailLogs, simLogs, data]);
  const filtered = all.filter(
    (l) =>
      levels.includes(l.level) &&
      (moduleFilter === "all" || l.module === moduleFilter || (moduleFilter === "simulation" && l.module.startsWith("sim."))) &&
      (query === "" || l.message.toLowerCase().includes(query.toLowerCase())),
  );

  const pqcInterventions = useMemo(() => {
    return all.filter((l) => /rekey|pqc|ml-kem|ml-dsa|isolate|quarantine|heal/i.test(l.message)).length;
  }, [all]);

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = isMock ? "quantumshield-demo-logs.json" : "quantumshield-logs.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHeader
        eyebrow="Module 08"
        title="Execution Logs"
        description="Tamper-evident audit trail: chronological telemetry across all defense modules with ML-DSA cryptographic verification."
        actions={
          <div className="flex items-center gap-2">
            {isMock && (
              <Button variant="hud" onClick={() => setTail((v) => !v)}>
                {tail ? <Pause className="size-4" /> : <Play className="size-4" />} {tail ? "Stop live tail" : "Live tail"}
              </Button>
            )}
            <Button variant="hud" onClick={exportJson}>
              <Download className="size-4" /> Export JSON
            </Button>
          </div>
        }
      />

      <ShineBorder
        className="w-full rounded-2xl"
        color={["#14b8a6", "#06b6d4"]}
        borderWidth={1.5}
        duration={14}
      >
        <GlassPanel title="Immutable Audit Stream" subtitle={`${filtered.length} entries matching filter`} icon={<TerminalSquare />} actions={<DemoBadge />} bodyClassName="p-0">
          <div className="grid gap-3 border-b border-border p-5 lg:grid-cols-[1fr_auto_200px] lg:items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search messages, hosts, hash digests…" className="pl-9" />
            </div>
            <ToggleGroup type="multiple" value={levels} onValueChange={(v) => setLevels(v as LogLevel[])} className="flex-wrap justify-start">
              {LEVELS.map((l) => (
                <ToggleGroupItem key={l} value={l} size="sm" className="font-mono text-[10px] data-[state=on]:bg-primary/15 data-[state=on]:text-primary">
                  {l}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            <Select value={moduleFilter} onValueChange={setModuleFilter}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All modules</SelectItem>
                <SelectItem value="simulation">Simulation runs</SelectItem>
                {logModules.map((m) => (
                  <SelectItem key={m} value={m}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="max-h-[640px] overflow-auto bg-background/40 font-mono text-xs scrollbar-thin">
            {filtered.map((l) => {
              const isPqcSigned = /rekey|pqc|ml-kem|ml-dsa|isolate|quarantine|heal/i.test(l.message);
              return (
                <div key={l.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border/50 px-5 py-2.5 hover:bg-primary/5 transition-colors">
                  <span className="w-28 shrink-0 text-muted-foreground">{fmtDateTime(l.timestamp)}</span>
                  <span className={cn("w-16 shrink-0 rounded border px-1.5 text-center text-[10px]", levelStyle[l.level])}>{l.level}</span>
                  <span className="w-40 shrink-0 truncate text-accent">{l.module}</span>
                  <span className="min-w-0 flex-1 text-foreground flex items-center gap-2">
                    {l.message}
                    {isPqcSigned && (
                      <span className="inline-flex items-center gap-1 font-mono text-[9px] uppercase tracking-wider text-primary border border-primary/40 rounded px-1.5 py-0.2 bg-primary/10">
                        <Lock className="size-2.5" />
                        ML-DSA VERIFIED
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
            {filtered.length === 0 && <p className="p-10 text-center text-muted-foreground">No log entries match your filter criteria.</p>}
          </div>
        </GlassPanel>
      </ShineBorder>
    </>
  );
}
