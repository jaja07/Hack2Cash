import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import AgentGraph from './AgentGraph'
import { useChat } from '../hooks/useChat'
import { uploadAndAnalyze } from '../api/client'

export default function ChatArea({ conversationId }) {
  // Appel avec un seul argument
  const { messages, status, agentStatuses, sendMessage } = useChat(conversationId);
  const [uploading, setUploading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

const handleFile = async (file) => {
  setUploading(true);
  try {
    // Étape 1 : Envoi physique au serveur (POST /api/agents/analyze/upload)
    await uploadAndAnalyze(file); 
    
    // Étape 2 : Confirmation visuelle
    // Vous pouvez utiliser une alerte standard ou un état pour afficher un badge
    alert(`Le fichier "${file.name}" a été téléchargé avec succès et est prêt pour l'analyse.`);
    
    console.log("Upload réussi. En attente d'une instruction utilisateur via le chat.");
  } catch (err) {
    console.error("Erreur lors de l'upload :", err);
    alert("Erreur lors du téléchargement du fichier.");
  } finally {
    setUploading(false); // Débloque l'icône trombone
  }
};

  return (
    <div className="flex flex-col h-screen flex-1 overflow-hidden bg-gray-950">
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm shrink-0">
        <div>
          <h2 className="font-semibold text-white text-sm">ARIA</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`} />
            <p className="text-gray-500 text-xs capitalize">{status}</p>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex flex-col flex-1 border-r border-gray-800 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

        <ChatInput 
          onSend={sendMessage} 
          onFile={handleFile} 
          disabled={status !== "connected"} // On ne bloque plus pendant l'upload
        />
        </div>

        <div className="w-96 bg-gray-900/30 flex flex-col overflow-hidden border-l border-gray-800">
          {/* Les animations se déclenchent ici via les agentStatuses */}
          <AgentGraph agentStatuses={agentStatuses} />
        </div>
      </div>
    </div>
  );
}