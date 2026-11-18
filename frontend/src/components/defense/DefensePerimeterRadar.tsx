import { motion } from "framer-motion";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface DefensePerimeterRadarProps {
  postureScore: number;
  isolatedCount?: number;
  totalNodes?: number;
  children: ReactNode;
  className?: string;
}

export function DefensePerimeterRadar({
  postureScore,
  isolatedCount = 0,
  totalNodes = 14,
  children,
  className,
}: DefensePerimeterRadarProps) {
  const isUnderAttack = postureScore < 60;
  const isAtRisk = postureScore < 80;

  // Concentric radar rings (from 21st.dev radar effect)
  const circles = [
    { size: 300, opacity: 0.12, border: "border-primary/25" },
    { size: 360, opacity: 0.18, border: "border-accent/30" },
    { size: 420, opacity: 0.10, border: "border-primary/20", dashed: true },
  ];

  // Defensive perimeter nodes orbiting the core
  const defenseNodes = [
    { label: "10.1.0.1", angle: 30, r: 155, isolated: isolatedCount > 0 },
    { label: "10.1.0.2", angle: 75, r: 175, isolated: isolatedCount > 1 },
    { label: "10.1.0.3", angle: 135, r: 160, isolated: isolatedCount > 2 },
    { label: "10.1.0.4", angle: 195, r: 180, isolated: false },
    { label: "10.1.0.7", angle: 240, r: 155, isolated: false },
    { label: "10.1.0.9", angle: 285, r: 170, isolated: false },
    { label: "10.1.0.12", angle: 330, r: 160, isolated: false },
  ];

  return (
    <div className={cn("relative grid place-items-center select-none py-6", className)}>
      <style>{`
        @keyframes defense-radar-spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        .animate-defense-radar {
          animation: defense-radar-spin 9s linear infinite;
        }
      `}</style>

      {/* Outer ambient glow */}
      <div
        className={cn(
          "pointer-events-none absolute size-96 rounded-full blur-3xl transition-colors duration-1000",
          isUnderAttack
            ? "bg-danger/20"
            : isAtRisk
            ? "bg-warning/15"
            : "bg-primary/15"
        )}
      />

      {/* Concentric radar rings */}
      {circles.map((c, i) => (
        <div
          key={i}
          className={cn(
            "pointer-events-none absolute rounded-full border transition-all duration-700",
            c.border,
            c.dashed && "border-dashed"
          )}
          style={{ width: c.size, height: c.size }}
        />
      ))}

      {/* Rotating radar sweep beam (21st.dev inspired) */}
      <div
        style={{ transformOrigin: "center center", width: 420, height: 420 }}
        className="pointer-events-none absolute animate-defense-radar"
      >
        <div className="absolute right-1/2 top-1/2 h-[2px] w-[210px] origin-left bg-gradient-to-r from-primary/80 via-primary/30 to-transparent" />
        <div
          className="absolute right-1/2 top-1/2 h-[210px] w-[210px] origin-top-left -translate-y-[210px] bg-gradient-to-tr from-primary/15 via-transparent to-transparent pointer-events-none"
          style={{
            clipPath: "polygon(0 100%, 100% 0, 100% 100%)",
          }}
        />
      </div>

      {/* Crosshairs & cardinal coordinate markings */}
      <div className="pointer-events-none absolute h-[430px] w-[1px] bg-gradient-to-b from-transparent via-primary/20 to-transparent" />
      <div className="pointer-events-none absolute h-[1px] w-[430px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />

      {/* Perimeter nodes mapped on the radar */}
      {defenseNodes.map((node, i) => {
        const rad = (node.angle * Math.PI) / 180;
        const x = Math.cos(rad) * node.r;
        const y = Math.sin(rad) * node.r;
        return (
          <div
            key={i}
            className="pointer-events-none absolute z-10 flex flex-col items-center"
            style={{
              transform: `translate(${x}px, ${y}px)`,
            }}
          >
            <span
              className={cn(
                "size-2.5 rounded-full border transition-all duration-500",
                node.isolated
                  ? "border-danger bg-danger shadow-[0_0_8px_rgba(239,68,68,0.9)] animate-ping"
                  : "border-primary bg-primary shadow-[0_0_8px_rgba(20,184,166,0.8)]"
              )}
            />
            <span className="mt-1 font-mono text-[9px] tracking-tighter text-muted-foreground/75 opacity-70">
              {node.label}
            </span>
          </div>
        );
      })}

      {/* Top and bottom status badges */}
      <div className="pointer-events-none absolute -top-2 flex items-center gap-1.5 rounded-full border border-primary/30 bg-background/80 px-2.5 py-0.5 font-mono text-[9px] uppercase tracking-widest text-primary backdrop-blur-md shadow-sm">
        {isAtRisk ? (
          <>
            <ShieldAlert className="size-3 text-warning" />
            <span>Perimeter Alert · {isolatedCount} Isolated</span>
          </>
        ) : (
          <>
            <ShieldCheck className="size-3 text-primary" />
            <span>360° PQC Shield Active · {totalNodes} Nodes</span>
          </>
        )}
      </div>

      {/* Center content (HudRing) */}
      <div className="relative z-20">
        {children}
      </div>
    </div>
  );
}
