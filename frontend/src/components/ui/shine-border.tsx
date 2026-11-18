import React from "react";
import { cn } from "@/lib/utils";

type TColorProp = string | string[];

interface ShineBorderProps {
  borderRadius?: number;
  borderWidth?: number;
  duration?: number;
  color?: TColorProp;
  className?: string;
  children: React.ReactNode;
}

export function ShineBorder({
  borderRadius = 12,
  borderWidth = 1.5,
  duration = 8,
  color = ["#14b8a6", "#a855f7", "#38bdf8"],
  className,
  children,
}: ShineBorderProps) {
  const colorStr = Array.isArray(color) ? color.join(",") : color;

  return (
    <div
      style={
        {
          "--border-radius": `${borderRadius}px`,
        } as React.CSSProperties
      }
      className={cn(
        "relative grid place-items-stretch rounded-[--border-radius] p-[1px] overflow-hidden",
        className
      )}
    >
      <style>{`
        @keyframes shine-spin {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .animate-shine-spin {
          animation: shine-spin ${duration}s ease infinite;
        }
      `}</style>
      <div
        style={
          {
            "--border-width": `${borderWidth}px`,
            "--border-radius": `${borderRadius}px`,
            backgroundImage: `linear-gradient(60deg, transparent 20%, ${colorStr}, transparent 80%)`,
            backgroundSize: "200% 200%",
          } as React.CSSProperties
        }
        className="pointer-events-none absolute inset-0 z-0 rounded-[--border-radius] animate-shine-spin opacity-75 blur-[0.5px]"
      />
      <div className="relative z-10 size-full rounded-[calc(var(--border-radius)-1px)] bg-card/90 backdrop-blur-xl">
        {children}
      </div>
    </div>
  );
}
