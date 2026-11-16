/**
 * Shared domain types for the QuantumShield AI frontend.
 * Shape your FastAPI response models (Pydantic) to match these, or adapt
 * them in src/services/quantumshield.service.ts.
 */

export type Tone = "primary" | "accent" | "success" | "warning" | "danger" | "muted";
export type Severity = "critical" | "high" | "medium" | "low";

export type NodeStatus = "healthy" | "warning" | "compromised" | "healing" | "isolated";
export type NodeType =
  | "gateway"
  | "firewall"
  | "router"
  | "switch"
  | "server"
  | "ai"
  | "pqc"
  | "iot"
  | "database"
  | "soc";
export type NodeLayer = "edge" | "core" | "service" | "endpoint";

export interface NetworkNode {
  id: string;
  label: string;
  type: NodeType;
  status: NodeStatus;
  layer: NodeLayer;
  /** Position on a 0–100 (x) by 0–60 (y) canvas. */
  x: number;
  y: number;
  ip: string;
  load: number;
}

export interface NetworkEdge {
  from: string;
  to: string;
  status?: "normal" | "congested" | "down" | "rerouted";
}

export interface Topology {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface KpiMetric {
  id: string;
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  tone: Tone;
  hint: string;
}

export interface TrafficPoint {
  time: string;
  inbound: number;
  outbound: number;
  anomalies: number;
}

export interface ThreatEvent {
  id: string;
  timestamp: string;
  category: string;
  severity: Severity;
  confidence: number;
  source: string;
  target: string;
  status: "blocked" | "monitoring" | "mitigated" | "investigating";
}

export interface RiskPoint {
  hour: string;
  predicted: number;
  observed: number;
}

export interface CategoryScore {
  category: string;
  score: number;
}

export interface ModelInfo {
  name: string;
  version: string;
  architecture: string;
  /** null = the backend has no measurement for this (it never invents one). */
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  /** Macro-F1 from the Stage 1 training run (backend/stage1 artifacts/metrics.json), when available. */
  macroF1?: number | null;
  /** ISO time, or "" when unknown. */
  lastTrained: string;
}

export interface OverviewData {
  postureScore: number;
  kpis: KpiMetric[];
  traffic: TrafficPoint[];
  recentThreats: ThreatEvent[];
}

export interface ThreatData {
  model: ModelInfo;
  currentRisk: number;
  riskTrend: RiskPoint[];
  categories: CategoryScore[];
  events: ThreatEvent[];
}

export interface PqcAlgorithm {
  id: string;
  name: string;
  family: string;
  role: "Key Encapsulation" | "Digital Signature";
  standard: string;
  securityLevel: number;
  status: "active" | "standby" | "testing";
  publicKeyBytes: number;
  usage: number;
  /** What `usage` measures. Defaults to "Traffic share" (demo data). */
  usageLabel?: string;
}

export interface CryptoSession {
  id: string;
  peer: string;
  kem: string;
  signature: string;
  mode: "hybrid" | "pqc-only" | "classical";
  established: string;
  latencyMs: number;
}

export interface HandshakeBenchmark {
  operation: string;
  /** null = no classical measurement exists (live backend). */
  classicalMs?: number | null;
  pqcMs: number;
}

export interface KeyRotationEvent {
  id: string;
  timestamp: string;
  algorithm: string;
  scope: string;
}

export interface CryptoData {
  coverage: number;
  algorithms: PqcAlgorithm[];
  sessions: CryptoSession[];
  benchmarks: HandshakeBenchmark[];
  rotations: KeyRotationEvent[];
}

export interface HealingIncident {
  id: string;
  timestamp: string;
  node: string;
  issue: string;
  action: string;
  durationSec: number;
  status: "resolved" | "in-progress" | "escalated";
}

export interface HealingPolicy {
  id: string;
  name: string;
  trigger: string;
  action: string;
  enabled: boolean;
}

export interface HealingData {
  mttrSeconds: number;
  autoRemediationRate: number;
  incidents: HealingIncident[];
  policies: HealingPolicy[];
  mttrTrend: { day: string; mttr: number; incidents: number }[];
}

export type PipelineStageStatus = "running" | "idle" | "degraded" | "error";

export interface PipelineStage {
  id: string;
  name: string;
  module: string;
  status: PipelineStageStatus;
  throughput: number;
  /** null = not measured by the backend. */
  latencyMs: number | null;
  queue: number;
  /** null = not measured by the backend. */
  uptime: number | null;
}

export interface PipelineData {
  stages: PipelineStage[];
  throughputHistory: { time: string; [stageId: string]: number | string }[];
}

export type LogLevel = "DEBUG" | "INFO" | "SUCCESS" | "WARN" | "ERROR";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
}

/* ----------------------------- Simulation ----------------------------- */

export type SimulationStageId = "traffic" | "detection" | "crypto" | "healing" | "final";

export type SimulationScenario = "ddos" | "lateral" | "hndl";

export interface SimulationConfig {
  scenario: SimulationScenario;
  intensity: number;
  nodes: number;
}

export interface SimulationStageResult {
  stageId: SimulationStageId;
  headline: string;
  metrics: { label: string; value: string }[];
  logs: { level: LogLevel; message: string }[];
}
