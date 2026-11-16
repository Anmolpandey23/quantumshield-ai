import { ShieldCheck } from "lucide-react";

export function BrandMark() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid size-10 place-items-center">
        <span className="absolute inset-0 rounded-lg border border-primary/40 animate-pulse-glow" />
        <span className="absolute inset-1 rounded-md bg-gradient-primary opacity-20" />
        <ShieldCheck className="relative size-5 text-primary" />
      </div>
      <div className="leading-tight">
        <p className="font-display text-base font-bold tracking-wide text-foreground">
          Quantum<span className="text-primary">Shield</span>
        </p>
        <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">AI · PQC · Self-Heal</p>
      </div>
    </div>
  );
}
