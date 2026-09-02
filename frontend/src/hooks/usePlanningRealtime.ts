"use client";

import { useEffect, useRef } from "react";
import { planningWsUrl } from "@/lib/api";

/** WebSocket — Planungsänderungen anderer Tabs/Benutzer nachladen. */
export function usePlanningRealtime(projectKey: string, onUpdate: () => void) {
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  useEffect(() => {
    if (!projectKey || typeof window === "undefined") return undefined;

    let closed = false;
    let ws: WebSocket | null = null;
    let retryMs = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (closed) return;
      const url = planningWsUrl(projectKey);
      if (!url) return;

      ws = new WebSocket(url);
      ws.onopen = () => {
        retryMs = 1000;
      };
      ws.onmessage = () => {
        onUpdateRef.current();
      };
      ws.onclose = () => {
        ws = null;
        if (!closed) {
          retryTimer = setTimeout(connect, retryMs);
          retryMs = Math.min(retryMs * 2, 30_000);
        }
      };
      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [projectKey]);
}
