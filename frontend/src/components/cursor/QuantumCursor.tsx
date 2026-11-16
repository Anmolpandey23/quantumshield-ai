import { useEffect, useRef, useState } from "react";

/**
 * Custom glowing cursor: dot + lagging ring + fading light trail + click ripple.
 * Only mounts on devices with a fine pointer that can hover (desktop mice/trackpads).
 * All layers are pointer-events:none, so clicks, text selection and inputs work normally.
 */
const INTERACTIVE =
  'a, button, summary, select, label, [role="button"], [role="link"], [role="tab"], [role="switch"], [role="checkbox"], [role="radio"], [role="option"], [role="menuitem"], [role="slider"], [data-cursor="hover"], svg g[style*="pointer"]';
const TEXT_INPUT =
  'input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="button"]):not([type="submit"]), textarea, [contenteditable="true"]';
const TRAIL_MS = 220;

export function QuantumCursor() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(hover: hover) and (pointer: fine)");
    const update = () => setEnabled(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  return enabled ? <CursorLayer /> : null;
}

function CursorLayer() {
  const rootRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    const dot = dotRef.current;
    const ring = ringRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!root || !dot || !ring || !canvas || !ctx) return;

    const html = document.documentElement;
    html.classList.add("qs-cursor-active");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const trailColor = getComputedStyle(html).getPropertyValue("--primary").trim() || "#22d3ee";

    const mouse = { x: -100, y: -100 };
    const ringPos = { x: -100, y: -100 };
    const points: { x: number; y: number; t: number }[] = [];
    let raf = 0;
    let last = performance.now();
    let visible = false;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const setState = (state: string) => {
      if (root.dataset["state"] !== state) root.dataset["state"] = state;
    };

    const onMove = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      if (!visible) {
        visible = true;
        ringPos.x = mouse.x;
        ringPos.y = mouse.y;
        root.dataset["visible"] = "true";
      }
      if (!reduceMotion) points.push({ x: mouse.x, y: mouse.y, t: performance.now() });
      const target = e.target instanceof Element ? e.target : null;
      if (target?.closest(TEXT_INPUT)) setState("text");
      else if (target?.closest(INTERACTIVE)) setState("hover");
      else setState("default");
    };

    const onDown = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      root.dataset["pressed"] = "true";
      const ripple = document.createElement("span");
      ripple.className = "qs-cursor-ripple";
      ripple.style.left = `${e.clientX}px`;
      ripple.style.top = `${e.clientY}px`;
      ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
      root.appendChild(ripple);
    };
    const onUp = () => {
      delete root.dataset["pressed"];
    };
    const onLeave = () => {
      visible = false;
      root.dataset["visible"] = "false";
      points.length = 0;
    };

    const tick = () => {
      const frameNow = performance.now();
      const dt = Math.min(64, frameNow - last);
      last = frameNow;
      // frame-rate independent smoothing (~0.25 per 60fps frame)
      const ease = reduceMotion ? 1 : 1 - Math.pow(0.75, dt / 16.67);
      ringPos.x += (mouse.x - ringPos.x) * ease;
      ringPos.y += (mouse.y - ringPos.y) * ease;
      dot.style.transform = `translate3d(${mouse.x}px, ${mouse.y}px, 0)`;
      ring.style.transform = `translate3d(${ringPos.x}px, ${ringPos.y}px, 0)`;

      // light trail
      const now = performance.now();
      while (points.length && now - (points[0]?.t ?? now) > TRAIL_MS) points.shift();
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      if (points.length > 1) {
        ctx.lineCap = "round";
        ctx.strokeStyle = trailColor;
        ctx.shadowColor = trailColor;
        ctx.shadowBlur = 8;
        for (let i = 1; i < points.length; i++) {
          const a = points[i - 1];
          const b = points[i];
          if (!a || !b) continue;
          const life = 1 - (now - b.t) / TRAIL_MS;
          ctx.globalAlpha = Math.max(0, life) * 0.55;
          ctx.lineWidth = 0.5 + life * 2.5;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerdown", onDown, { passive: true });
    window.addEventListener("pointerup", onUp, { passive: true });
    window.addEventListener("resize", resize);
    document.documentElement.addEventListener("mouseleave", onLeave);
    window.addEventListener("blur", onLeave);

    return () => {
      cancelAnimationFrame(raf);
      html.classList.remove("qs-cursor-active");
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("resize", resize);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      window.removeEventListener("blur", onLeave);
    };
  }, []);

  return (
    <div ref={rootRef} className="qs-cursor" data-state="default" data-visible="false" aria-hidden>
      <canvas ref={canvasRef} className="qs-cursor-trail" />
      <div ref={ringRef} className="qs-cursor-ring" />
      <div ref={dotRef} className="qs-cursor-dot" />
    </div>
  );
}
