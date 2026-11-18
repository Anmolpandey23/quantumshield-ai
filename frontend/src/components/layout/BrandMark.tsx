export function BrandMark() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid size-10 place-items-center">
        <span className="absolute inset-0 rounded-lg border border-primary/40 animate-pulse-glow" />
        <span className="absolute inset-1 rounded-md bg-gradient-primary opacity-20" />
        <img
          src="/shield-icon.png"
          alt="QuantumShield Emblem"
          className="relative size-7 object-contain drop-shadow-[0_0_8px_rgba(20,184,166,0.7)]"
        />
      </div>
      <div className="leading-tight">
        <p className="font-display text-base font-bold tracking-wide text-foreground">
          Quantum<span className="text-primary">Shield</span> <span className="text-accent text-xs font-mono font-normal">AI</span>
        </p>
        <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Predict · Protect · Self-Heal</p>
      </div>
    </div>
  );
}
