import { createRng, range } from "@/lib/seeded";
import type { OverviewData, TrafficPoint } from "@/types/quantumshield";
import { mockThreatEvents } from "./threats";

/** DEMO DATA — sample values for UI preview only. */
function buildTraffic(): TrafficPoint[] {
  const rng = createRng(42);
  return Array.from({ length: 24 }, (_, i) => {
    const wave = Math.sin(i / 3) * 140;
    const inbound = Math.round(620 + wave + range(rng, -60, 60));
    return {
      time: `${String(i).padStart(2, "0")}:00`,
      inbound,
      outbound: Math.round(inbound * range(rng, 0.55, 0.75)),
      anomalies: Math.round(i === 14 || i === 15 ? range(rng, 60, 90) : range(rng, 2, 18)),
    };
  });
}

export const mockOverview: OverviewData = {
  postureScore: 87,
  kpis: [
    { id: "threats", label: "Threats Blocked (24h)", value: "1,284", delta: "+12.4%", trend: "up", tone: "primary", hint: "Sample count" },
    { id: "health", label: "Network Health", value: "96.2%", delta: "+0.8%", trend: "up", tone: "success", hint: "14 nodes monitored" },
    { id: "pqc", label: "PQC Coverage", value: "78%", delta: "+6.0%", trend: "up", tone: "accent", hint: "Hybrid + PQC-only links" },
    { id: "mttr", label: "Mean Time to Heal", value: "42s", delta: "-18s", trend: "down", tone: "warning", hint: "Automated remediation" },
  ],
  traffic: buildTraffic(),
  recentThreats: mockThreatEvents.slice(0, 5),
};
