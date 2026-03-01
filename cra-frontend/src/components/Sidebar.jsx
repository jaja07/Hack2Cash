/**
 * components/Sidebar.jsx
 * Left panel: branding, navigation, file upload trigger, history.
 */
import { useAuth } from '../context/AuthContext'

const NAV = [
  { icon: '💬', label: 'Activity Report Analysis' },
  { icon: '📊', label: 'Reports' },
  { icon: '🔍', label: 'History' },
]

export default function Sidebar({ activeSection, onSection, onNewChat }) {
  const { user, logout } = useAuth()

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen">

      {/* Brand */}
      <div className="px-5 py-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-sm">📈</div>
          <span className="font-bold text-white text-lg">CRA Analyzer</span>
        </div>
      </div>

      {/* New Chat */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-700
                     hover:bg-gray-800 text-gray-300 hover:text-white text-sm transition"
        >
          <span className="text-base">＋</span>
          New analysis
        </button>
      </div>

      {/* Nav */}
      <nav className="px-3 flex-1 space-y-1 overflow-y-auto scrollbar-thin">
        {NAV.map(({ icon, label }) => (
          <button
            key={label}
            onClick={() => onSection?.(label)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition
              ${activeSection === label
                ? 'bg-brand-700 text-white font-medium'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
          >
            <span>{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-800">
          <div className="w-7 h-7 rounded-full bg-brand-500 flex items-center justify-center text-xs font-bold text-white">
            {user?.username?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <span className="flex-1 text-sm text-gray-300 truncate">{user?.username}</span>
          <button
            onClick={logout}
            title="Log out"
            className="text-gray-500 hover:text-red-400 transition text-base"
          >
            ⏻
          </button>
        </div>
      </div>
    </aside>
  )
}
