import { motion } from "framer-motion";
import {
  BrainCircuit,
  Cpu,
  Database,
  Globe,
  KeyRound,
  MonitorDot,
  Network,
  Router,
  Server,
  ShieldHalf,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { NetworkEdge, NetworkNode, NodeStatus, NodeType, Topology } from "@/types/quantumshield";

const typeIcon: Record<NodeType, LucideIcon> = {
  gateway: Globe,
  firewall: ShieldHalf,
  router: Router,
  switch: Network,
  server: Server,
  ai: BrainCircuit,
  pqc: KeyRound,
  iot: Cpu,
  database: Database,
  soc: MonitorDot,
};

export const statusColor: Record<NodeStatus, string> = {
  healthy: "var(--color-success)",
  warning: "var(--color-warning)",
  compromised: "var(--color-destructive)",
  healing: "var(--color-accent)",
  isolated: "var(--color-muted-foreground)",
};

const edgeColor: Record<NonNullable<NetworkEdge["status"]>, string> = {
  normal: "var(--color-primary)",
  congested: "var(--color-warning)",
  down: "var(--color-destructive)",
  rerouted: "var(--color-accent)",
};

interface NetworkGraphProps {
  topology: Topology;
  selectedId?: string | null | undefined;
  onSelect?: (node: NetworkNode) => void;
  showLabels?: boolean;
  dimmedIds?: Set<string>;
  className?: string;
}

/** Animated SVG network map: glowing links, travelling packets, pulsing nodes. */
export function NetworkGraph({
  topology,
  selectedId,
  onSelect,
  showLabels = true,
  dimmedIds,
  className,
}: NetworkGraphProps) {
  const byId = new Map(topology.nodes.map((n) => [n.id, n]));

  return (
    <svg
      viewBox="-5 -3 110 68"
      className={cn("h-full w-full select-none", className)}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Network topology map (demo data)"
    >
      <defs>
        <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="0.8" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <radialGradient id="node-fill">
          <stop offset="0%" stopColor="var(--color-surface-raised)" />
          <stop offset="100%" stopColor="var(--color-background)" />
        </radialGradient>
      </defs>

      {topology.edges.map((e, i) => {
        const a = byId.get(e.from);
        const b = byId.get(e.to);
        if (!a || !b) return null;
        const status = e.status ?? "normal";
        const color = edgeColor[status];
        const dim = dimmedIds && (dimmedIds.has(a.id) || dimmedIds.has(b.id));
        const path = `M ${a.x} ${a.y} L ${b.x} ${b.y}`;
        return (
          <g key={`${e.from}-${e.to}`} opacity={dim ? 0.15 : 1}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={color} strokeOpacity={0.12} strokeWidth={1.2} />
            <line
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={color}
              strokeOpacity={status === "down" ? 0.55 : 0.7}
              strokeWidth={0.25}
              strokeDasharray={status === "down" ? "0.8 1.2" : "2 1"}
              className={status === "down" ? undefined : "animate-dash"}
            />
            {status !== "down" && (
              <circle r={0.45} fill={color} filter="url(#node-glow)">
                <animateMotion dur={`${2.2 + (i % 5) * 0.5}s`} repeatCount="indefinite" path={path} begin={`${(i % 7) * 0.3}s`} />
              </circle>
            )}
          </g>
        );
      })}

      {topology.nodes.map((n, i) => {
        const Icon = typeIcon[n.type];
        const color = statusColor[n.status];
        const selected = selectedId === n.id;
        const dim = dimmedIds?.has(n.id);
        const alert = n.status === "compromised" || n.status === "healing";
        return (
          <motion.g
            key={n.id}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: dim ? 0.25 : 1, scale: 1 }}
            transition={{ delay: i * 0.03, duration: 0.4 }}
            style={{ transformOrigin: `${n.x}px ${n.y}px`, cursor: onSelect ? "pointer" : "default" }}
            onClick={() => onSelect?.(n)}
          >
            {alert && (
              <circle cx={n.x} cy={n.y} r={3.4} fill="none" stroke={color} strokeWidth={0.2}>
                <animate attributeName="r" values="2.6;4.6;2.6" dur="1.8s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.9;0;0.9" dur="1.8s" repeatCount="indefinite" />
              </circle>
            )}
            {selected && (
              <circle cx={n.x} cy={n.y} r={3.6} fill="none" stroke="var(--color-primary)" strokeWidth={0.25} strokeDasharray="1 0.6" className="animate-dash" />
            )}
            <circle cx={n.x} cy={n.y} r={2.6} fill="url(#node-fill)" stroke={color} strokeWidth={0.3} filter="url(#node-glow)" />
            <Icon x={n.x - 1.3} y={n.y - 1.3} width={2.6} height={2.6} color={color} strokeWidth={1.6} />
            {showLabels && (
              <text
                x={n.x}
                y={n.y + 4.6}
                textAnchor="middle"
                fontSize={1.6}
                fill="var(--color-muted-foreground)"
                fontFamily="var(--font-mono)"
              >
                {n.label}
              </text>
            )}
          </motion.g>
        );
      })}
    </svg>
  );
}

export function NetworkLegend() {
  const items: [string, string][] = [
    ["Healthy", statusColor.healthy],
    ["Warning", statusColor.warning],
    ["Compromised", statusColor.compromised],
    ["Healing", statusColor.healing],
    ["Isolated", statusColor.isolated],
  ];
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
      {items.map(([label, color]) => (
        <span key={label} className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
          {label}
        </span>
      ))}
    </div>
  );
}
