/**
 * components/MessageBubble.jsx
 * Single chat message — user or assistant.
 * Intègre le rendu Markdown riche et l'indicateur de streaming.
 */
import FormattedResponse from './FormattedResponse';

function AgentBadge({ agent }) {
  const colors = {
    supervisor:    'bg-purple-900 text-purple-300',
    web_research:  'bg-blue-900 text-blue-300',
    tool_builder:  'bg-yellow-900 text-yellow-300',
    analysis:      'bg-green-900 text-green-300',
    system:        'bg-gray-800 text-gray-400',
  };
  const cls = colors[agent] ?? 'bg-gray-800 text-gray-400';
  return (
    <span className={`inline-block text-xs px-2 py-0.5 rounded font-mono mb-1 ${cls}`}>
      {agent}
    </span>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  // Détermine si le message est actuellement en cours de génération
  const isStreaming = !isUser && message.isStreaming;

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      {/* Avatar — assistant */}
      {!isUser && (
        <div className="w-8 h-8 flex-shrink-0 rounded-full bg-brand-600 flex items-center justify-center text-sm mt-1 shadow-lg shadow-brand-900/20">
          🤖
        </div>
      )}

      <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Agent badge */}
        {!isUser && message.agent && <AgentBadge agent={message.agent} />}

        {/* Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-xl
            ${isUser
              ? 'bg-brand-600 text-white rounded-tr-sm'
              : 'bg-gray-800 text-gray-100 rounded-tl-sm border border-gray-700'
            }`}
        >
          {isUser ? (
            // Rendu simple pour l'utilisateur
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            // Rendu stylisé (Markdown + Tableaux) pour l'assistant
            <FormattedResponse 
              content={message.content} 
              isStreaming={isStreaming} 
            />
          )}
        </div>

        {/* Timestamp */}
        {message.timestamp && (
          <span className="text-gray-600 text-[10px] mt-1 px-1">
            {new Date(message.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {/* Avatar — user */}
      {isUser && (
        <div className="w-8 h-8 flex-shrink-0 rounded-full bg-gray-700 flex items-center justify-center text-sm mt-1">
          👤
        </div>
      )}
    </div>
  );
}