/** Fixed reference time for demo data (keeps SSR + client output identical). */
export const DEMO_EPOCH = Date.UTC(2026, 10, 14, 16, 0, 0);

export function isoMinusMinutes(minutes: number) {
  return new Date(DEMO_EPOCH - minutes * 60_000).toISOString();
}
