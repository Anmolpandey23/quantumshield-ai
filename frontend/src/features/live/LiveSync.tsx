import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useLiveFeed } from "./useLiveFeed";
import { API_BASE_URL, API_KEY } from "@/services/api/config";
import { wsUrl } from "./ws-url";

/**
 * Live mode only. Keeps one WebSocket to the backend open (auto-reconnect) and, whenever the backend reports a
 * change, refetches every active query so all pages follow the pipeline in real time. Renders nothing.
 */
export function LiveSync() {
  const queryClient = useQueryClient();
  const { isLive } = useLiveFeed();

  useEffect(() => {
    if (!isLive) return;
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
      if (closed) return;
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
      socket.onerror = () => {
        // Handled silently; reconnect loop is triggered via onclose
      };
      socket.onclose = () => {
        if (!closed) scheduleReconnect();
      };
    }

    connect();
    return () => {
      closed = true;
      clearTimeout(retryTimer);
      clearTimeout(refreshTimer);
      if (socket) {
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;
        if (socket.readyState === WebSocket.OPEN) {
          socket.close(1000, "LiveSync unmounted");
        } else if (socket.readyState === WebSocket.CONNECTING) {
          // If still connecting, wait for open before closing to avoid browser abort warning
          socket.onopen = () => {
            try {
              socket?.close(1000, "LiveSync unmounted");
            } catch {}
          };
        }
      }
    };
  }, [queryClient, isLive]);

  return null;
}
