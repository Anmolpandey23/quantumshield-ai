import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const fill = {
  primary: "bg-primary",
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-destructive",
} as const;

/** Thin animated horizontal meter. */
export function Meter({
  value,
  tone = "primary",
  className,
}: {
  value: number;
  tone?: keyof typeof fill;
  className?: string;
}) {
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-muted", className)}>
      <motion.div
        className={cn("h-full rounded-full", fill[tone])}
        initial={{ width: 0 }}
        animate={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        transition={{ duration: 0.9, ease: "easeOut" }}
      />
    </div>
  );
}

export function loadTone(v: number): keyof typeof fill {
  return v > 85 ? "danger" : v > 70 ? "warning" : "primary";
}
