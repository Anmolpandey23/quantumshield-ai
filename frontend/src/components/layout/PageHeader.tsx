import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { DemoBadge } from "@/components/hud/DemoBadge";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between"
    >
      <div className="flex items-start gap-3.5">
        <div className="hidden sm:flex size-11 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 p-1.5 shadow-[0_0_15px_rgba(20,184,166,0.2)]">
          <img
            src="/shield-icon.png"
            alt="QuantumShield"
            className="size-full object-contain filter drop-shadow-[0_0_6px_rgba(20,184,166,0.6)]"
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="h-px w-6 bg-primary" />
            <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-primary">{eyebrow}</p>
            <DemoBadge />
          </div>
          <h1 className="mt-1.5 text-3xl font-semibold text-foreground md:text-4xl">{title}</h1>
          {description && <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{description}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </motion.div>
  );
}
