import { QueryClient } from "@tanstack/react-query";
import { createRouter, rootRouteId } from "@tanstack/react-router";
import { describe, expect, it } from "vitest";
import { mockStageResult } from "@/data/mock/simulation";
import { SIMULATION_STAGES } from "@/features/simulation/stages";
import { routeTree } from "@/routeTree.gen";

describe("End-to-end workflow", () => {
  it("runs Network Traffic → AI Threat Detection → Quantum-Safe Security → Self-Healing → Final Status", () => {
    expect(SIMULATION_STAGES.map((s) => s.label)).toEqual([
      "Network Traffic",
      "AI Threat Detection",
      "Quantum-Safe Security",
      "Self-Healing",
      "Final Status",
    ]);
  });

  it("returns a demo result for every stage", () => {
    for (const s of SIMULATION_STAGES) {
      const r = mockStageResult(s.id, { scenario: "ddos", intensity: 50, nodes: 10 });
      expect(r.stageId).toBe(s.id);
    }
  });
});

describe("Dashboard pages", () => {
  const paths = ["/", "/threats", "/cryptography", "/self-healing", "/topology", "/pipeline", "/simulation", "/logs"];
  it.each(paths)("has a page for %s", (path) => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });
    expect(router.matchRoutes(path).at(-1)?.routeId).not.toBe(rootRouteId);
  });
});
