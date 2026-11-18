import type { ReactNode } from "react";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  const { isLive } = useLiveFeed();
  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 hud-grid" aria-hidden />
      <AppSidebar />
      <div className="relative lg:pl-64">
        <TopBar />
        <main className="mx-auto w-full max-w-[1500px] px-4 py-6 md:px-8 md:py-8">{children}</main>
        <footer className="px-4 pb-8 flex flex-col items-center justify-center gap-2 text-center font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60 md:px-8">
          <div className="flex items-center gap-2">
            <img src="/shield-icon.png" alt="QuantumShield Logo" className="size-4 object-contain opacity-80" />
            <span className="font-semibold text-foreground/80">QuantumShield AI</span>
            <span>·</span>
            <span className="text-primary/90">Predict · Protect · Self-Heal</span>
          </div>
          <p>{isLive ? "Live backend · Simulation Center runs inject synthetic attacks" : "Frontend preview · All values are simulated demo data"}</p>
        </footer>
      </div>
    </div>
  );
}
