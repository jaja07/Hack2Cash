import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const MAX_RECONNECT_DELAY = 30000;

export function useChat(token, conversationId) {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("disconnected"); // "disconnected" | "connecting" | "connected" | "thinking"
  const wsRef = useRef(null);
  const reconnectDelay = useRef(1000);
  const intentionalClose = useRef(false);

  const connect = useCallback(() => {
    if (!conversationId || !token) return;

    setStatus("connecting");
    const ws = new WebSocket(`${WS_URL}/ws/${conversationId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectDelay.current = 1000;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "history") {
        // Remplace les messages par l'historique reçu à la connexion
        setMessages(data.messages);
        setStatus("connected");

      } else if (data.type === "message") {
        setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
        setStatus("connected");

      } else if (data.type === "status" && data.content === "thinking") {
        setStatus("thinking");

      } else if (data.type === "error") {
        console.error("Erreur WebSocket :", data.content);
        setStatus("connected");
      }
    };

    ws.onclose = () => {
      // Fermeture volontaire (changement de conversation) : on ne reconnecte pas
      if (intentionalClose.current) {
        intentionalClose.current = false;
        return;
      }

      setStatus("disconnected");
      setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => setStatus("disconnected");
  }, [token, conversationId]);

  // Reconnecte à chaque changement de conversation
  useEffect(() => {
    setMessages([]);

    if (wsRef.current) {
      intentionalClose.current = true;
      wsRef.current.close(1000);
    }

    connect();

    return () => {
      intentionalClose.current = true;
      wsRef.current?.close(1000);
    };
  }, [connect]);

  const sendMessage = useCallback((content) => {
    if (!content.trim() || wsRef.current?.readyState !== WebSocket.OPEN) return;

    setMessages((prev) => [...prev, { role: "user", content }]);
    wsRef.current.send(JSON.stringify({ content }));
  }, []);

  return { messages, status, sendMessage };
}