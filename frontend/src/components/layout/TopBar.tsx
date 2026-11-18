import { Menu, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/hud/StatusBadge";
import { RunSimulationButton } from "@/components/simulation/RunSimulationButton";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useSimulation } from "@/features/simulation/SimulationProvider";
import { useLiveFeed } from "@/features/live/useLiveFeed";
import { cn } from "@/lib/utils";
import { BrandMark } from "./BrandMark";
import { SidebarFooter } from "./AppSidebar";
import { SidebarNav } from "./SidebarNav";

function Clock() {
  const [now, setNow] = useState<string | null>(null);
  useEffect(() => {
    const tick = () => setNow(new Date().toISOString().slice(11, 19));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);
  return <span className="font-mono text-xs tabular-nums text-muted-foreground">{now ?? "--:--:--"} UTC</span>;
}

export function TopBar() {
  const [open, setOpen] = useState(false);
  const { status } = useSimulation();
  const { isLive, toggle: toggleLiveFeed } = useLiveFeed();
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-3 px-4 md:px-8">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="hud" size="icon" className="lg:hidden" aria-label="Open navigation">
              <Menu />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 border-sidebar-border bg-popover p-0">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <div className="p-5">
              <BrandMark />
            </div>
            <div className="px-3">
              <SidebarNav onNavigate={() => setOpen(false)} />
            </div>
            <SidebarFooter />
          </SheetContent>
        </Sheet>

        <div className="flex items-center gap-2 lg:hidden">
          <img src="/shield-icon.png" alt="QuantumShield Logo" className="size-6 object-contain drop-shadow-[0_0_6px_rgba(20,184,166,0.6)]" />
          <span className="font-display text-sm font-bold tracking-wide text-foreground">
            Quantum<span className="text-primary">Shield</span> <span className="text-accent text-[10px] font-mono">AI</span>
          </span>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <StatusBadge tone="success" pulse>
            Systems nominal
          </StatusBadge>
          <span className="hidden xl:inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 font-mono text-[10px] text-primary">
            <ShieldCheck className="size-3 text-primary animate-pulse" />
            14 Fleet Nodes Shielded (FIPS 203)
          </span>
          {status === "running" && (
            <StatusBadge tone="primary" pulse>
              Simulation running
            </StatusBadge>
          )}
          <span className="hidden 2xl:inline">
            <Clock />
          </span>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <button
            type="button"
            onClick={toggleLiveFeed}
            title={isLive ? "Click to pause live feed and switch to simulated demo data" : "Click to connect to live backend"}
            className={cn(
              "hidden rounded border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider transition-all sm:inline-flex items-center gap-1.5 cursor-pointer shadow-sm hover:scale-[1.02]",
              isLive
                ? "border-primary/40 bg-primary/10 text-primary hover:bg-primary/20 shadow-[0_0_10px_rgba(20,184,166,0.25)]"
                : "border-warning/40 bg-warning/10 text-warning hover:bg-warning/20 shadow-[0_0_10px_rgba(245,158,11,0.25)]",
            )}
          >
            <span className={cn("size-1.5 rounded-full", isLive ? "bg-primary animate-pulse" : "bg-warning")} />
            {isLive ? "Live backend · active" : "Demo mode · simulated data"}
          </button>
          <RunSimulationButton size="sm" />
        </div>
      </div>
    </header>
  );
}
