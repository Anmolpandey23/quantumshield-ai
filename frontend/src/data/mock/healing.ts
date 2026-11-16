import type { HealingData } from "@/types/quantumshield";
import { isoMinusMinutes } from "./helpers";

/** DEMO DATA — sample remediation history. */
export const mockHealing: HealingData = {
  mttrSeconds: 42,
  autoRemediationRate: 91,
  incidents: [
    { id: "HEAL-311", timestamp: isoMinusMinutes(4), node: "sw-b", issue: "Anomalous east-west traffic", action: "Isolated port group, rerouted via core-2", durationSec: 38, status: "in-progress" },
    { id: "HEAL-310", timestamp: isoMinusMinutes(27), node: "iot", issue: "Firmware integrity mismatch", action: "Rolled back to signed image", durationSec: 64, status: "resolved" },
    { id: "HEAL-309", timestamp: isoMinusMinutes(96), node: "fw-2", issue: "CPU saturation (SYN flood)", action: "Scaled rate limits, shifted load to fw-1", durationSec: 21, status: "resolved" },
    { id: "HEAL-308", timestamp: isoMinusMinutes(180), node: "core-1", issue: "BGP route flap", action: "Pinned stable route, dampened peer", durationSec: 47, status: "resolved" },
    { id: "HEAL-307", timestamp: isoMinusMinutes(320), node: "db", issue: "Unauthorized query burst", action: "Revoked session, rotated credentials", durationSec: 112, status: "escalated" },
  ],
  policies: [
    { id: "p1", name: "Auto-isolate compromised nodes", trigger: "Threat confidence ≥ 0.90", action: "Quarantine VLAN + reroute", enabled: true },
    { id: "p2", name: "Dynamic path rerouting", trigger: "Link loss or latency > 200ms", action: "Recompute shortest secure path", enabled: true },
    { id: "p3", name: "Firmware rollback", trigger: "Signature verification failure", action: "Restore last ML-DSA signed image", enabled: true },
    { id: "p4", name: "Key re-negotiation", trigger: "Suspected key compromise", action: "Force ML-KEM rekey on affected tunnels", enabled: false },
  ],
  mttrTrend: [
    { day: "Mon", mttr: 71, incidents: 9 },
    { day: "Tue", mttr: 64, incidents: 12 },
    { day: "Wed", mttr: 58, incidents: 7 },
    { day: "Thu", mttr: 52, incidents: 14 },
    { day: "Fri", mttr: 47, incidents: 10 },
    { day: "Sat", mttr: 45, incidents: 6 },
    { day: "Sun", mttr: 42, incidents: 8 },
  ],
};
