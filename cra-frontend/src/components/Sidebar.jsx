import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import logoImage from '../assets/technology_1.webp';
import PricingModal from './PricingModal';

/**
 * Sidebar Component
 * Gère la navigation principale, l'historique des analyses,
 * ainsi que l'accès au Pricing et à l'Aide.
 */
export default function Sidebar({ 
  activeSection, 
  onSection, 
  onNewChat, 
  conversations = [], 
  onSelectConv, 
  activeConvId 
}) {
  const { user, logout } = useAuth();
  const [isPricingOpen, setIsPricingOpen] = useState(false); // Gère l'affichage du modal de pricing
  
  const isHistoryView = activeSection === 'History';

  return (
    <>
      <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen font-sans">
        
        {/* LOGO & BRAND */}
        <div className="p-5 border-b border-gray-800 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center bg-gray-800 shadow-inner">
            <img 
              src={logoImage} 
              alt="ARIA Logo" 
              className="w-full h-full object-cover" 
            />
          </div>
          <span className="font-bold text-white tracking-tight text-lg">ARIA</span>
        </div>

        {/* NAVIGATION PRINCIPALE */}
        <nav className="px-3 flex-1 space-y-1 overflow-y-auto mt-6 scrollbar-thin">
          {!isHistoryView ? (
            <>
              {/* BOUTON NOUVELLE ANALYSE */}
              <button
                onClick={onNewChat}
                className="w-full flex items-center gap-2 px-4 py-3 mb-6 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold transition-all shadow-lg shadow-brand-900/20 group"
              >
                <span className="text-xl group-hover:scale-125 transition-transform">+</span> 
                New Analysis
              </button>

              {/* ANALYSE COURANTE */}
              <button
                onClick={() => onSection('Analyse CRA')}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activeSection === 'Analyse CRA' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:bg-gray-800/50'
                }`}
              >
                <span className="text-base">📊</span> Current Analysis
              </button>

              {/* VOIR L'HISTORIQUE */}
              <button
                onClick={() => onSection('History')}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800/50 transition-colors"
              >
                <span className="text-base">📜</span> View History
              </button>

              {/* --- SECTION OUTILS COMPLÉMENTAIRES --- */}
              <div className="pt-4 mt-4 border-t border-gray-800 space-y-1">
                {/* BOUTON PRICING */}
                <button
                  onClick={() => setIsPricingOpen(true)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800/50 transition-colors group"
                >
                  <span className="text-base group-hover:scale-110 transition-transform">💎</span> 
                  Pricing
                </button>

                {/* BOUTON HELP (STATIQUE) */}
                <button
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800/50 transition-colors cursor-default"
                >
                  <span className="text-base">❓</span> 
                  Help
                </button>
              </div>
            </>
          ) : (
            /* VUE HISTORIQUE DES RAPPORTS */
            <div className="animate-in slide-in-from-left duration-200">
              <button
                onClick={() => onSection('Analyse CRA')}
                className="flex items-center gap-2 text-[10px] text-brand-400 hover:text-brand-300 mb-6 px-3 font-bold uppercase tracking-widest transition-colors"
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
                        onSection('Analyse CRA');
                      }}
                      className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all truncate group
                        ${activeConvId === conv.id
                          ? 'bg-gray-800 text-white border-l-2 border-brand-500'
                          : 'text-gray-500 hover:bg-gray-800 hover:text-gray-200'}`}
                    >
                      <div className="truncate font-medium group-hover:translate-x-1 transition-transform">
                        {conv.title || "Untitled Analysis"}
                      </div>
                      <div className="text-[10px] opacity-40 mt-0.5 italic">
                         {new Date(conv.created_at).toLocaleDateString('fr-FR')}
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

        {/* PROFILE & LOGOUT */}
        <div className="p-4 border-t border-gray-800 bg-gray-900/50">
          <div className="flex items-center justify-between gap-3 px-2">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 shadow-md">
                {user?.prenom?.[0]}{user?.nom?.[0]}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate">
                  {user?.prenom} {user?.nom}
                </p>
                <p className="text-[10px] text-gray-500 truncate lowercase">{user?.email}</p>
              </div>
            </div>
            
            <button 
              onClick={logout}
              title="Déconnexion"
              className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* MODAL DE PRICING */}
      <PricingModal 
        isOpen={isPricingOpen} 
        onClose={() => setIsPricingOpen(false)} 
      />
    </>
  );
}