/** http(s)://host:8000 -> ws(s)://host:8000/ws?api_key=KEY  (the backend's live feed). */
export function wsUrl(base: string, key: string): string {
  const u = new URL(base);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  u.pathname = `${u.pathname.replace(/\/+$/, "")}/ws`;
  u.search = key ? `?api_key=${encodeURIComponent(key)}` : "";
  u.hash = "";
  return u.toString();
}
