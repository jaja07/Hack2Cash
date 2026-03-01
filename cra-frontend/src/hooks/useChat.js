import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const MAX_RECONNECT_DELAY = 30000;

export function useChat(conversationId) {
  // 1. Déclaration des States (DOIVENT être en premier)
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("disconnected");
  const [agentStatuses, setAgentStatuses] = useState({}); // Pour piloter le graphe
  
  // 2. Déclaration des Refs
  const wsRef = useRef(null);
  const reconnectDelay = useRef(1000);
  const intentionalClose = useRef(false);

  const connect = useCallback(() => {
    const token = sessionStorage.getItem('cra_token'); // Récupération interne du token
    if (!conversationId || !token) return;

    setStatus("connecting");
    // Utilisation du préfixe /api/ws pour correspondre au backend FastAPI
    const ws = new WebSocket(`${WS_URL}/api/ws/${conversationId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectDelay.current = 1000;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "history":
          setMessages(data.messages);
          setStatus("connected");
          break;
        case "message":
          setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
          setStatus("connected");
          break;
        case "status":
          if (data.agent) {
            // Met à jour l'agent spécifique (ex: 'analysis') pour l'animation
            setAgentStatuses(prev => ({ ...prev, [data.agent]: data.content }));
          } else {
            setStatus(data.content);
          }
          break;
        case "error":
          console.error("Erreur WebSocket :", data.content);
          setStatus("connected");
          break;
      }
    };

    ws.onclose = () => {
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
  }, [conversationId]); // Seul conversationId est une dépendance

  useEffect(() => {
    setMessages([]);
    setAgentStatuses({}); // Reset du graphe au changement de conversation
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

  return { messages, status, agentStatuses, sendMessage };
}