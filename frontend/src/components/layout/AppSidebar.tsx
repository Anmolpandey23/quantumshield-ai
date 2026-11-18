import { useLiveFeed } from "@/features/live/useLiveFeed";
import { BrandMark } from "./BrandMark";
import { SidebarNav } from "./SidebarNav";

export function AppSidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar backdrop-blur-xl lg:flex">
      <div className="px-5 py-5">
        <BrandMark />
      </div>
      <div className="mx-5 h-px bg-gradient-to-r from-transparent via-border-strong to-transparent" />
      <div className="flex-1 overflow-y-auto px-3 py-5 scrollbar-thin">
        <p className="mb-2 px-3 font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground/70">Modules</p>
        <SidebarNav />
      </div>
      <SidebarFooter />
    </aside>
  );
}

export function SidebarFooter() {
  const { isLive } = useLiveFeed();
  return (
    <div className="m-3 rounded-lg border border-border bg-surface/60 p-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Data source</p>
      <p className="mt-1 text-xs text-foreground font-medium">
        {isLive ? "QuantumShield Core (Live)" : "Demo dataset (Simulated)"}
      </p>
      <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
        {isLive
          ? "Live real-time telemetry from the active QuantumShield defense pipeline."
          : "All figures shown are sample values for UI preview — not real security results."}
      </p>
    </div>
  );
}
