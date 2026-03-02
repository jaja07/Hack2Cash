import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import AgentGraph from './AgentGraph'
import Toast from './Toast'
import { useChat } from '../hooks/useChat'
import { uploadForWebsocket } from '../api/client'

export default function ChatArea({ conversationId }) {
  const { messages, status, agentStatuses, sendMessage } = useChat(conversationId);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);
  const [attachedFile, setAttachedFile] = useState(null); // État pour stocker le fichier chargé
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFile = async (file) => {
    setUploading(true);
    try {
      await uploadForWebsocket(conversationId, file);
      setAttachedFile(file); // Enregistre le fichier pour l'affichage en bas à droite
      setToast({ 
        message: `File '${file.name}' ready for analysis.`, 
        type: 'success' 
      });
    } catch (err) {
      console.error("Erreur lors de l'upload :", err);
      setToast({ 
        message: "Error uploading file.", 
        type: 'error' 
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen flex-1 overflow-hidden bg-gray-950">
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}

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
        {/* Colonne de gauche : Chat */}
        <div className="flex flex-col flex-1 border-r border-gray-800 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="px-4">
            {uploading && (
              <div className="py-2 flex items-center gap-2 text-indigo-400 animate-pulse text-xs italic">
                <span>⏳ Téléchargement du document...</span>
              </div>
            )}
          </div>

          <ChatInput 
            onSend={sendMessage} 
            onFile={handleFile} 
            disabled={status !== "connected"} 
          />
        </div>

        {/* Colonne de droite : Graphe (Haut) et Documents (Bas) */}
        <div className="w-96 bg-gray-900/30 flex flex-col overflow-hidden border-l border-gray-800">
          
          {/* Section Graphe : Remonte vers le haut grâce à flex-1 */}
          <div className="flex-1 overflow-hidden flex flex-col border-b border-gray-800">
            <AgentGraph agentStatuses={agentStatuses} />
          </div>

          {/* Section : Documents Envoyés (fixée en bas) */}
          <div className="h-64 flex flex-col bg-gray-900/50">
            <div className="p-3 border-b border-white/5 bg-gray-800/40 flex justify-between items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                Uploaded Documents
              </span>
              <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 text-[9px] font-bold">
                {attachedFile ? '1' : '0'}
              </span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
              {attachedFile ? (
                <div className="flex items-center gap-3 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 animate-in fade-in zoom-in duration-300 shadow-sm text-left">
                  <div className="w-10 h-10 rounded-lg bg-indigo-600/20 flex items-center justify-center text-xl shadow-inner">
                    📄
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-gray-100 truncate" title={attachedFile.name}>
                      {attachedFile.name}
                    </p>


                  </div>
                  <button onClick={() => setAttachedFile(null)} className="text-gray-500 hover:text-white transition-colors">✕</button>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center opacity-20 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                  <span className="text-3xl mb-2">📁</span>
                  <p className="text-[10px] uppercase font-bold tracking-widest">No file</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}