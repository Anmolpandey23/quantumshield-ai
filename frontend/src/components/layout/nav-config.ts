import {
  Activity,
  BrainCircuit,
  FlaskConical,
  HeartPulse,
  KeyRound,
  LayoutDashboard,
  Share2,
  TerminalSquare,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to:
    | "/"
    | "/threats"
    | "/cryptography"
    | "/self-healing"
    | "/topology"
    | "/pipeline"
    | "/simulation"
    | "/logs";
  label: string;
  icon: LucideIcon;
  code: string;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Overview", icon: LayoutDashboard, code: "01" },
  { to: "/threats", label: "AI Threat Prediction", icon: BrainCircuit, code: "02" },
  { to: "/cryptography", label: "Quantum Cryptography", icon: KeyRound, code: "03" },
  { to: "/self-healing", label: "Self-Healing Network", icon: HeartPulse, code: "04" },
  { to: "/topology", label: "Network Topology", icon: Share2, code: "05" },
  { to: "/pipeline", label: "Pipeline Monitor", icon: Activity, code: "06" },
  { to: "/simulation", label: "Simulation Center", icon: FlaskConical, code: "07" },
  { to: "/logs", label: "Execution Logs", icon: TerminalSquare, code: "08" },
];
