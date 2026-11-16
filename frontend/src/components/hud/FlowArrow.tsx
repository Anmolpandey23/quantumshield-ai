import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export type FlowState = "idle" | "active" | "done";

const stroke: Record<FlowState, string> = {
  idle: "var(--color-primary)",
  active: "var(--color-primary)",
  done: "var(--color-success)",
};

/**
 * Themed animated connector: glowing track, flowing dashes and
 * cascading chevrons. Horizontal on large screens, vertical on mobile.
 */
export function FlowArrow({
  state = "idle",
  horizontalAt = "lg",
  className,
}: {
  state?: FlowState;
  /** Breakpoint at which the arrow points right instead of down. */
  horizontalAt?: "lg" | "xl";
  className?: string;
}) {
  const color = stroke[state];
  const speed = state === "active" ? 0.9 : state === "done" ? 1.6 : 2.2;
  const peak = state === "idle" ? 0.55 : 1;

  return (
    <div
      aria-hidden
      className={cn("flex shrink-0 items-center justify-center py-1", className)}
    >
      <svg viewBox="0 0 44 18" className={cn("h-[18px] w-10 rotate-90 overflow-visible", horizontalAt === "lg" ? "lg:rotate-0" : "xl:rotate-0")}>
        <defs>
          <linearGradient id={`flow-${state}`} x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor={color} stopOpacity="0" />
            <stop offset="60%" stopColor={color} stopOpacity="0.8" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="1" />
          </linearGradient>
        </defs>
        {/* track */}
        <line x1="2" y1="9" x2="36" y2="9" stroke={color} strokeOpacity="0.15" strokeWidth="3" strokeLinecap="round" />
        <line
          x1="2"
          y1="9"
          x2="36"
          y2="9"
          stroke={`url(#flow-${state})`}
          strokeWidth="1.2"
          strokeDasharray="4 4"
          className="animate-dash"
          style={{ animationDuration: `${speed}s` }}
        />
        {/* cascading chevrons */}
        {[0, 1, 2].map((i) => (
          <motion.path
            key={i}
            d={`M ${10 + i * 8} 4.5 L ${14.5 + i * 8} 9 L ${10 + i * 8} 13.5`}
            fill="none"
            stroke={color}
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ opacity: 0.15 }}
            animate={{ opacity: [0.15, peak, 0.15], x: [0, 1.5, 0] }}
            transition={{ duration: speed, repeat: Infinity, delay: (i * speed) / 4, ease: "easeInOut" }}
            style={{ filter: `drop-shadow(0 0 2px ${color})` }}
          />
        ))}
        {/* glowing head */}
        <motion.path
          d="M 36 3.5 L 42 9 L 36 14.5"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: speed, repeat: Infinity }}
          style={{ filter: "drop-shadow(0 0 3px var(--color-accent))" }}
        />
        {/* travelling packet */}
        {state !== "idle" && (
          <circle r="1.6" cy="9" fill="var(--color-primary-glow)" style={{ filter: "drop-shadow(0 0 3px var(--color-primary))" }}>
            <animate attributeName="cx" values="2;38" dur={`${speed}s`} repeatCount="indefinite" />
            <animate attributeName="opacity" values="0;1;0" dur={`${speed}s`} repeatCount="indefinite" />
          </circle>
        )}
      </svg>
    </div>
  );
}
