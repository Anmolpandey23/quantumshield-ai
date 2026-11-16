import { motion } from "framer-motion";
import type { ReactNode } from "react";

/** JARVIS-style concentric animated ring with a score in the centre. */
export function HudRing({
  value,
  label,
  sublabel,
  size = 240,
  children,
}: {
  value: number;
  label?: string;
  sublabel?: ReactNode;
  size?: number;
  children?: ReactNode;
}) {
  const r = 82;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 200 200" className="absolute inset-0 size-full">
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" />
            <stop offset="100%" stopColor="var(--color-accent)" />
          </linearGradient>
        </defs>
        <g className="origin-center animate-spin-slow" style={{ transformBox: "fill-box" }}>
          <circle cx="100" cy="100" r="96" fill="none" stroke="var(--color-primary)" strokeOpacity="0.35" strokeWidth="0.6" strokeDasharray="2 6" />
        </g>
        <g className="origin-center animate-spin-reverse" style={{ transformBox: "fill-box" }}>
          <circle cx="100" cy="100" r="90" fill="none" stroke="var(--color-accent)" strokeOpacity="0.5" strokeWidth="1.2" strokeDasharray="40 18 6 18" />
        </g>
        <circle cx="100" cy="100" r={r} fill="none" stroke="var(--color-muted)" strokeWidth="6" />
        <motion.circle
          cx="100"
          cy="100"
          r={r}
          fill="none"
          stroke="url(#ring-grad)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - value / 100) }}
          transition={{ duration: 1.6, ease: "easeOut" }}
          transform="rotate(-90 100 100)"
          style={{ filter: "drop-shadow(0 0 6px var(--color-primary))" }}
        />
        <circle cx="100" cy="100" r="68" fill="none" stroke="var(--color-primary)" strokeOpacity="0.15" strokeWidth="0.8" />
        {Array.from({ length: 60 }, (_, i) => (
          <line
            key={i}
            x1="100"
            y1="26"
            x2="100"
            y2={i % 5 === 0 ? 31 : 29}
            stroke="var(--color-primary)"
            strokeOpacity={i % 5 === 0 ? 0.6 : 0.25}
            strokeWidth="0.6"
            transform={`rotate(${i * 6} 100 100)`}
          />
        ))}
      </svg>
      <div className="relative text-center">
        {children ?? (
          <>
            <p className="font-display text-5xl font-bold text-glow text-primary tabular-nums">{value}</p>
            {label && (
              <p className="mt-1 text-[10px] uppercase tracking-[0.25em] text-muted-foreground">{label}</p>
            )}
            {sublabel && <div className="mt-2">{sublabel}</div>}
          </>
        )}
      </div>
    </div>
  );
}
