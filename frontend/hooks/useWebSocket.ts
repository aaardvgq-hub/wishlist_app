"use client";

import { useEffect, useRef, useCallback } from "react";

const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_MS = 1000;
const MAX_RECONNECT_MS = 30000;

function getWsBase(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (apiUrl) {
    const u = apiUrl.replace(/\/api\/?$/, "").replace(/^http/, "ws");
    return u;
  }
  if (typeof window !== "undefined")
    return `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
  return "";
}

export function useWishlistWebSocket(
  wishlistId: string | null,
  onMessage: (data: { event: string; wishlist_id: string; payload: unknown }) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    const base = getWsBase();
    if (!wishlistId || !base) return;
    const url = `${base}/api/ws/${wishlistId}`;
    const ws = new WebSocket(url);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessageRef.current(data);
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      // Connection failed; onclose will run and trigger reconnect
    };

    ws.onclose = () => {
      wsRef.current = null;
      const attempt = reconnectAttemptRef.current;
      if (attempt >= MAX_RECONNECT_ATTEMPTS) return;
      const delay = Math.min(
        INITIAL_RECONNECT_MS * Math.pow(2, attempt),
        MAX_RECONNECT_MS
      );
      reconnectAttemptRef.current = attempt + 1;
      reconnectTimerRef.current = setTimeout(() => {
        reconnectTimerRef.current = null;
        connect();
      }, delay);
    };

    ws.onopen = () => {
      reconnectAttemptRef.current = 0;
    };

    wsRef.current = ws;
  }, [wishlistId]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      reconnectAttemptRef.current = MAX_RECONNECT_ATTEMPTS;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const reconnect = useCallback(() => {
    reconnectAttemptRef.current = 0;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    connect();
  }, [connect]);

  return { reconnect };
}
