import type { ReactNode } from "react";
import { USE_MOCK_DATA } from "@/services/api/config";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 hud-grid" aria-hidden />
      <AppSidebar />
      <div className="relative lg:pl-64">
        <TopBar />
        <main className="mx-auto w-full max-w-[1500px] px-4 py-6 md:px-8 md:py-8">{children}</main>
        <footer className="px-4 pb-8 text-center font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60 md:px-8">
          {USE_MOCK_DATA ? "QuantumShield AI · Frontend preview · All values are simulated demo data" : "QuantumShield AI · Live backend · Simulation Center runs inject synthetic attacks"}
        </footer>
      </div>
    </div>
  );
}
