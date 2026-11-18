import { FlaskConical } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLiveFeed } from "@/features/live/useLiveFeed";

/**
 * Marks any surface showing simulated / sample values.
 * Hidden when the dashboard runs on the live backend, unless `always` is set (used for surfaces that stay
 * simulated even then, such as the Simulation Center and the browser-only demos).
 */
export function DemoBadge({ className, label = "Demo data", always = false }: { className?: string; label?: string; always?: boolean }) {
  const { isLive } = useLiveFeed();
  if (isLive && !always) return null;
  return (
    <span
      title="Sample values for UI preview only — not real security results"
      className={cn(
        "inline-flex items-center gap-1 rounded border border-warning/30 bg-warning/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-warning",
        className,
      )}
    >
      <FlaskConical className="size-3" />
      {label}
    </span>
  );
}
