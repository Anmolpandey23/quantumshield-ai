import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { Tone } from "@/types/quantumshield";

const toneText: Record<Tone, string> = {
  primary: "text-primary",
  accent: "text-accent",
  success: "text-success",
  warning: "text-warning",
  danger: "text-destructive",
  muted: "text-muted-foreground",
};
const toneBar: Record<Tone, string> = {
  primary: "bg-primary",
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-destructive",
  muted: "bg-muted-foreground",
};

export function StatCard({
  label,
  value,
  delta,
  trend = "flat",
  tone = "primary",
  hint,
  icon,
  index = 0,
}: {
  label: string;
  value: ReactNode;
  delta?: string;
  trend?: "up" | "down" | "flat";
  tone?: Tone;
  hint?: string;
  icon?: ReactNode;
  index?: number;
}) {
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4 }}
      whileHover={{ y: -3 }}
      className="glass group relative overflow-hidden rounded-xl p-5"
    >
      <span className={cn("absolute inset-x-0 top-0 h-px opacity-70", toneBar[tone])} />
      <div className="flex items-start justify-between">
        <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
          {label}
        </p>
        {icon && <span className={cn("[&_svg]:size-4", toneText[tone])}>{icon}</span>}
      </div>
      <p className={cn("mt-3 font-display text-3xl font-semibold tabular-nums", toneText[tone])}>
        {value}
      </p>
      <div className="mt-2 flex items-center justify-between text-xs">
        {delta && (
          <span className="inline-flex items-center gap-1 font-mono text-foreground/80">
            <TrendIcon className="size-3.5" />
            {delta}
          </span>
        )}
        {hint && <span className="text-muted-foreground">{hint}</span>}
      </div>
    </motion.div>
  );
}
