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
      <div>
        <div className="flex items-center gap-2">
          <span className="h-px w-6 bg-primary" />
          <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-primary">{eyebrow}</p>
          <DemoBadge />
        </div>
        <h1 className="mt-2 text-3xl font-semibold text-foreground md:text-4xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </motion.div>
  );
}
