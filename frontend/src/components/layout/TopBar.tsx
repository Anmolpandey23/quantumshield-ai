import { Menu } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/hud/StatusBadge";
import { RunSimulationButton } from "@/components/simulation/RunSimulationButton";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useSimulation } from "@/features/simulation/SimulationProvider";
import { USE_MOCK_DATA } from "@/services/api/config";
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

        <div className="hidden items-center gap-3 md:flex">
          <StatusBadge tone="success" pulse>
            Systems nominal
          </StatusBadge>
          {status === "running" && (
            <StatusBadge tone="primary" pulse>
              Simulation running
            </StatusBadge>
          )}
          <span className="hidden xl:inline">
            <Clock />
          </span>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <span className="hidden rounded border border-warning/30 bg-warning/10 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-warning sm:inline">
            {USE_MOCK_DATA ? "Demo mode · simulated data" : "Live backend"}
          </span>
          <RunSimulationButton size="sm" />
        </div>
      </div>
    </header>
  );
}
