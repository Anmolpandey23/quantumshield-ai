import { motion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface GlassPanelProps extends Omit<HTMLMotionProps<"section">, "title"> {
  title?: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  corners?: boolean;
  bodyClassName?: string;
  children?: ReactNode;
}

/** The base glass card used across every dashboard page. */
export function GlassPanel({
  title,
  subtitle,
  icon,
  actions,
  corners = true,
  className,
  bodyClassName,
  children,
  ...rest
}: GlassPanelProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className={cn("glass min-w-0 rounded-xl", corners && "hud-corners", className)}
      {...rest}
    >
      {(title || actions) && (
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            {icon && (
              <span className="grid size-8 shrink-0 place-items-center rounded-md border border-border-strong bg-primary/10 text-primary [&_svg]:size-4">
                {icon}
              </span>
            )}
            <div className="min-w-0">
              {title && (
                <h3 className="truncate text-sm font-semibold uppercase tracking-[0.14em] text-foreground">
                  {title}
                </h3>
              )}
              {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
            </div>
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cn("p-5", bodyClassName)}>{children}</div>
    </motion.section>
  );
}
