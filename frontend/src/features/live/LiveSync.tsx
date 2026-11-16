import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { API_BASE_URL, API_KEY, USE_MOCK_DATA } from "@/services/api/config";
import { wsUrl } from "./ws-url";

/**
 * Live mode only. Keeps one WebSocket to the backend open (auto-reconnect) and, whenever the backend reports a
 * change, refetches every active query so all pages follow the pipeline in real time. Renders nothing.
 */
export function LiveSync() {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (USE_MOCK_DATA) return;
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;
    let closed = false;
    let attempt = 0;

    const refresh = () => {
      clearTimeout(refreshTimer);
      refreshTimer = setTimeout(() => {
        void queryClient.invalidateQueries();
      }, 400);
    };

    const scheduleReconnect = () => {
      attempt += 1;
      retryTimer = setTimeout(connect, Math.min(10_000, 1_000 * attempt));
    };

    function connect() {
      try {
        socket = new WebSocket(wsUrl(API_BASE_URL, API_KEY));
      } catch {
        scheduleReconnect();
        return;
      }
      socket.onopen = () => {
        attempt = 0;
        refresh();
      };
      socket.onmessage = refresh;
      socket.onclose = () => {
        if (!closed) scheduleReconnect();
      };
    }

    connect();
    return () => {
      closed = true;
      clearTimeout(retryTimer);
      clearTimeout(refreshTimer);
      socket?.close();
    };
  }, [queryClient]);

  return null;
}
