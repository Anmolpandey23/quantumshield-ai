import type { TooltipProps } from "recharts";

/** Shared Recharts styling bound to design tokens. */
export const chartColors = {
  primary: "var(--color-chart-1)",
  accent: "var(--color-chart-2)",
  info: "var(--color-chart-3)",
  warning: "var(--color-chart-4)",
  danger: "var(--color-chart-5)",
  grid: "var(--color-border)",
  axis: "var(--color-muted-foreground)",
};

export const axisProps = {
  stroke: chartColors.axis,
  fontSize: 11,
  tickLine: false,
  axisLine: false,
  fontFamily: "var(--font-mono)",
} as const;

export function HudTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs">
      <p className="mb-1 font-mono text-muted-foreground">{label}</p>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center gap-2">
          <span className="size-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground">{p.name}</span>
          <span className="ml-auto font-mono text-foreground">
            {typeof p.value === "number" ? p.value.toLocaleString("en-US") : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}
