import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { isLiveFeedActive, setLiveFeedActive } from "@/services/api/config";

export function useLiveFeed() {
  const queryClient = useQueryClient();
  const [isLive, setIsLiveState] = useState<boolean>(() => isLiveFeedActive());

  useEffect(() => {
    const handleFeedChange = (e: Event) => {
      const customEvent = e as CustomEvent<boolean>;
      setIsLiveState(customEvent.detail);
      void queryClient.invalidateQueries();
    };

    window.addEventListener("qs_live_feed_change", handleFeedChange);
    return () => {
      window.removeEventListener("qs_live_feed_change", handleFeedChange);
    };
  }, [queryClient]);

  const setLive = useCallback(
    (next: boolean, notify = true) => {
      setIsLiveState(next);
      setLiveFeedActive(next);
      void queryClient.invalidateQueries();

      if (notify) {
        if (next) {
          toast.success("Live Feed Resumed", {
            description: "Streaming real-time telemetry from QuantumShield defense pipeline",
          });
        } else {
          toast.info("Live Feed Paused · Demo Mode Active", {
            description: "All pages now display simulated demo telemetry",
          });
        }
      }
    },
    [queryClient],
  );

  const toggle = useCallback(() => {
    setLive(!isLive);
  }, [isLive, setLive]);

  return {
    isLive,
    isMock: !isLive,
    setLive,
    toggle,
  };
}
