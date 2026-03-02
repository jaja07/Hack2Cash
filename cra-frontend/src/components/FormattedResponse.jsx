import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function FormattedResponse({ content, isStreaming }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none text-gray-200">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Stylisation des tableaux (ex: TRIZ Analysis)
          table: ({ children }) => (
            <div className="overflow-x-auto my-4 rounded-lg border border-gray-700 bg-gray-900/50">
              <table className="min-w-full divide-y divide-gray-800">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="px-4 py-2 bg-gray-800/50 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{children}</th>,
          td: ({ children }) => <td className="px-4 py-2 text-sm border-t border-gray-800">{children}</td>,
          // Stylisation des titres et texte important
          h2: ({children}) => <h2 className="text-indigo-400 mt-6 mb-2 uppercase tracking-wide text-[10px] font-bold">{children}</h2>,
          strong: ({children}) => <span className="text-brand-400 font-semibold">{children}</span>,
        }}
      >
        {content}
      </ReactMarkdown>
      
      {/* Curseur de simulation de streaming */}
      {isStreaming && (
        <span className="inline-block w-1.5 h-4 bg-indigo-500 animate-pulse ml-1 align-middle" />
      )}
    </div>
  );
}