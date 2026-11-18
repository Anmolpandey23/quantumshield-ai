/** UTC-based formatting so SSR and browser output always match. */
export const fmtTime = (iso: string) => iso.slice(11, 19);
export const fmtDateTime = (iso: string) => `${iso.slice(5, 10)} ${iso.slice(11, 16)}`;

/** Format seconds into human-readable duration: "42s", "57m 39s", "1h 12m" */
export function formatDuration(val: number | string | undefined | null): string {
  if (val === undefined || val === null || val === "" || val === "—") return "—";
  let sec: number;
  if (typeof val === "string") {
    if (val.endsWith("s")) {
      const parsed = parseFloat(val.slice(0, -1));
      if (isNaN(parsed)) return val;
      sec = Math.round(parsed);
    } else {
      const parsed = parseFloat(val);
      if (isNaN(parsed)) return val;
      sec = Math.round(parsed);
    }
  } else {
    sec = Math.round(val);
  }

  if (sec <= 0) return "—";
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (sec < 3600) {
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  }
  const h = Math.floor(sec / 3600);
  const remM = Math.floor((sec % 3600) / 60);
  return remM > 0 ? `${h}h ${remM}m` : `${h}h`;
}

