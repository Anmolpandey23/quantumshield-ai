import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const badge = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wider whitespace-nowrap",
  {
    variants: {
      tone: {
        primary: "border-primary/30 bg-primary/10 text-primary",
        accent: "border-accent/30 bg-accent/10 text-accent",
        success: "border-success/30 bg-success/10 text-success",
        warning: "border-warning/30 bg-warning/10 text-warning",
        danger: "border-destructive/40 bg-destructive/10 text-destructive",
        muted: "border-border bg-muted/60 text-muted-foreground",
        info: "border-info/30 bg-info/10 text-info",
      },
    },
    defaultVariants: { tone: "primary" },
  },
);

export type BadgeTone = NonNullable<VariantProps<typeof badge>["tone"]>;

const dotTone: Record<BadgeTone, string> = {
  primary: "bg-primary",
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-destructive",
  muted: "bg-muted-foreground",
  info: "bg-info",
};

export function StatusBadge({
  tone = "primary",
  pulse,
  className,
  children,
}: {
  tone?: BadgeTone | undefined;
  pulse?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span className={cn(badge({ tone }), className)}>
      <span className="relative flex size-1.5">
        {pulse && (
          <span className={cn("absolute inline-flex size-full animate-ping rounded-full opacity-70", dotTone[tone])} />
        )}
        <span className={cn("relative inline-flex size-1.5 rounded-full", dotTone[tone])} />
      </span>
      {children}
    </span>
  );
}

/* Common status → tone mappings */
export const severityTone: Record<string, BadgeTone> = {
  critical: "danger",
  high: "warning",
  medium: "info",
  low: "muted",
};

export const nodeStatusTone: Record<string, BadgeTone> = {
  healthy: "success",
  warning: "warning",
  compromised: "danger",
  healing: "accent",
  isolated: "muted",
};
