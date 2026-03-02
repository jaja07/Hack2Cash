import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL ?? "wss://hack2cashbackend-production-30f3.up.railway.app";
const MAX_RECONNECT_DELAY = 30000;

export function useChat(conversationId) {
  // 1. Déclaration des States
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("disconnected");
  const [agentStatuses, setAgentStatuses] = useState({}); 
  
  // 2. Déclaration des Refs
  const wsRef = useRef(null);
  const reconnectDelay = useRef(1000);
  const intentionalClose = useRef(false);

  const connect = useCallback(() => {
    const token = sessionStorage.getItem('cra_token'); 
    if (!conversationId || !token) return;

    setStatus("connecting");
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
          const fullContent = data.content;
          let currentText = "";
          let charIndex = 0;

          // 1. Initialise un message vide avec le flag de streaming actif
          setMessages((prev) => [...prev, { role: "assistant", content: "", isStreaming: true }]);

          // 2. Déclenche l'intervalle d'écriture progressive
          const typingInterval = setInterval(() => {
            // On avance par blocs de 15 caractères pour maintenir une vitesse de lecture confortable
            charIndex += 40; 
            currentText = fullContent.slice(0, charIndex);

            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = { 
                  ...updated[updated.length - 1], 
                  content: currentText 
                };
              }
              return updated;
            });

            // 3. Arrêt une fois la totalité du texte affichée
            if (charIndex >= fullContent.length) {
              clearInterval(typingInterval);
              setMessages((prev) => {
                const finished = [...prev];
                if (finished.length > 0) {
                  finished[finished.length - 1].isStreaming = false; // Retire le curseur
                }
                return finished;
              });
            }
          }, 30); // 30ms permet une animation fluide sans saccades

          setStatus("connected");
          break;

        case "agent_step":
          setAgentStatuses(prev => ({ 
            ...prev, 
            [data.node]: data.status 
          }));
          break;

        case "status":
          setStatus(data.content);
          if (data.content === "agent_starting") {
            setAgentStatuses({}); 
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
  }, [conversationId]);

  useEffect(() => {
    setMessages([]);
    setAgentStatuses({}); 
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