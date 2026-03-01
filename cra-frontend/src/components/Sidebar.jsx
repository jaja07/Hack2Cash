// src/components/Sidebar.jsx

export default function Sidebar({ 
  activeSection, 
  onSection, 
  onNewChat, 
  conversations = [], 
  onSelectConv, 
  activeConvId 
}) {
  // Détermine si on affiche la liste de l'historique ou le menu principal
  const isHistoryView = activeSection === 'History';

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen font-sans">
      {/* BRAND / LOGO */}
      <div className="p-5 border-b border-gray-800 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold">
          A
        </div>
        <span className="font-bold text-white tracking-tight">CRA ANALYZER</span>
      </div>

      <nav className="px-3 flex-1 space-y-1 overflow-y-auto mt-6">
        {!isHistoryView ? (
          /* --- VUE INITIALE (Navigation) --- */
          <>
            {/* BOUTON CRÉER : Appelle la fonction onNewChat du Dashboard */}
            <button
              onClick={onNewChat}
              className="w-full flex items-center gap-2 px-4 py-3 mb-6 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold transition-all shadow-lg shadow-brand-900/20 group"
            >
              <span className="text-xl group-hover:scale-125 transition-transform">+</span> 
              New Analysis
            </button>

            <button
              onClick={() => onSection('Analyse CRA')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                activeSection === 'Analyse CRA' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800/50'
              }`}
            >
              <span className="text-base">📊</span> Current Analysis
            </button>

            {/* BOUTON HISTORIQUE : Bascule la vue pour afficher la liste */}
            <button
              onClick={() => onSection('History')}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800/50 transition-colors"
            >
              <span className="text-base">📜</span> View History
            </button>
          </>
        ) : (
          /* --- VUE HISTORIQUE (S'affiche après clic sur History) --- */
          <div className="animate-in slide-in-from-left duration-200">
            <button
              onClick={() => onSection('Analyse CRA')}
              className="flex items-center gap-2 text-[10px] text-brand-400 hover:text-brand-300 mb-6 px-3 font-bold uppercase tracking-widest"
            >
              ← Back to Menu
            </button>
            
            <h3 className="px-3 text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">
              Past Reports
            </h3>
            
            <div className="space-y-1">
              {conversations.length > 0 ? (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => {
                      onSelectConv(conv.id);
                      onSection('Analyse CRA'); // Retourne au chat après sélection
                    }}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all truncate group
                      ${activeConvId === conv.id
                        ? 'bg-gray-800 text-white border-l-2 border-brand-500'
                        : 'text-gray-500 hover:bg-gray-800 hover:text-gray-200'}`}
                  >
                    <div className="truncate font-medium group-hover:translate-x-1 transition-transform">
                      {conv.title || "Untitled Analysis"}
                    </div>
                    <div className="text-[10px] opacity-40 mt-0.5">
                       {new Date(conv.created_at).toLocaleDateString()}
                    </div>
                  </button>
                ))
              ) : (
                <p className="px-3 text-xs text-gray-600 italic">No history found.</p>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* FOOTER */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/50">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-gray-700 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-white truncate">User Account</p>
          </div>
        </div>
      </div>
    </aside>
  );
}