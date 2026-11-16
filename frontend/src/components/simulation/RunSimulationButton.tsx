import { Link } from "@tanstack/react-router";
import { Loader2, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSimulation } from "@/features/simulation/SimulationProvider";

export function RunSimulationButton({
  size = "default",
  showLink = false,
}: {
  size?: "default" | "sm" | "lg" | "xl";
  showLink?: boolean;
}) {
  const { status, progress, run, reset } = useSimulation();
  const running = status === "running";
  return (
    <div className="flex items-center gap-2">
      <Button variant="hero" size={size} onClick={run} disabled={running}>
        {running ? <Loader2 className="animate-spin" /> : <Play />}
        {running ? `Simulating ${progress}%` : status === "complete" ? "Run Again" : "Run End-to-End Simulation"}
      </Button>
      {status === "complete" && (
        <Button variant="hud" size="icon" onClick={reset} aria-label="Reset simulation">
          <RotateCcw />
        </Button>
      )}
      {showLink && (
        <Button variant="hud" size={size} asChild>
          <Link to="/simulation">Open Simulation Center</Link>
        </Button>
      )}
    </div>
  );
}
