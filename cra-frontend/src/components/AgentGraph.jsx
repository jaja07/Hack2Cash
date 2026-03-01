/**
 * components/AgentGraph.jsx
 */

const AGENTS = [
  { key: 'supervisor',   label: 'Supervisor',     icon: '⚡', color: '#6366F1', x: 200, y: 180 },
  { key: 'web_research', label: 'Web Research',   icon: '🌐', color: '#3B82F6', x: 200, y: 80  },
  { key: 'tool_builder', label: 'Tool Builder',   icon: '🔧', color: '#8B5CF6', x: 340, y: 180 },
  { key: 'analysis',     label: 'Analysis',       icon: '🧠', color: '#10B981', x: 200, y: 280 },
  { key: 'output',       label: 'Output',         icon: '📁', color: '#F59E0B', x: 60,  y: 180 },
];

// Liens unidirectionnels pour l'animation des flux
const EDGES = [
  { from: 'supervisor', to: 'web_research' },
  { from: 'supervisor', to: 'tool_builder' },
  { from: 'supervisor', to: 'analysis' },
  { from: 'supervisor', to: 'output' },
];

function AgentNode({ agent, status }) {
  const isRunning = status === 'running';
  const isDone = status === 'completed';

  const color = isDone ? '#10B981' : isRunning ? agent.color : 'rgba(255,255,255,0.1)';
  const stroke = isDone ? '#10B981' : isRunning ? agent.color : 'rgba(255,255,255,0.2)';

  return (
    <g transform={`translate(${agent.x},${agent.y})`} className="transition-all duration-500">
      {/* Halo d'animation quand l'agent travaille */}
      {isRunning && (
        <circle r="30" fill="none" stroke={agent.color} strokeWidth="1" opacity="0.5">
          <animate attributeName="r" from="22" to="35" dur="1.5s" repeatCount="indefinite" />
          <animate attributeName="opacity" from="0.5" to="0" dur="1.5s" repeatCount="indefinite" />
        </circle>
      )}
      
      <circle 
        r="22" 
        fill={color} 
        stroke={stroke} 
        strokeWidth={isRunning ? 3 : 1}
        className="transition-colors duration-500"
        style={{ filter: isRunning ? `drop-shadow(0 0 8px ${agent.color})` : 'none' }}
      />
      
      <text textAnchor="middle" dominantBaseline="middle" fontSize="16" y="1">{agent.icon}</text>
      
      <text textAnchor="middle" y="38" fontSize="10" fontWeight={isRunning || isDone ? "bold" : "normal"}
            fill={isDone ? '#10B981' : isRunning ? 'white' : 'rgba(255,255,255,0.4)'}>
        {agent.label}
      </text>

      {isDone && (
        <circle r="8" cx="15" cy="-15" fill="#10B981" stroke="#000" strokeWidth="1">
           <title>Terminé</title>
        </circle>
      )}
    </g>
  );
}

export default function AgentGraph({ agentStatuses = {} }) {
  // Le backend renvoie un objet comme { supervisor: 'running', web_research: 'idle', ... }
  const getStatus = (key) => agentStatuses[key] || 'idle';

  return (
    <div className="flex flex-col h-full w-full bg-gray-900/50">
      <div className="p-4 border-b border-white/5 flex justify-between items-center">
        <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Pipeline Status</span>
        <div className="flex gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <svg viewBox="0 0 400 360" className="w-full h-full max-w-[400px]">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="rgba(255,255,255,0.2)" />
            </marker>
          </defs>

          {/* Dessin des liens avec animation de flux si le supervisor est actif */}
          {EDGES.map((edge, i) => {
            const from = AGENTS.find(a => a.key === edge.from);
            const to = AGENTS.find(a => a.key === edge.to);
            const active = getStatus(edge.to) === 'running';

            return (
              <g key={i}>
                <line 
                  x1={from.x} y1={from.y} x2={to.x} y2={to.y} 
                  stroke="rgba(255,255,255,0.1)" strokeWidth="1" strokeDasharray="4 4"
                />
                {active && (
                  <circle r="3" fill="#6366F1">
                    <animateMotion 
                      path={`M ${from.x} ${from.y} L ${to.x} ${to.y}`} 
                      dur="1s" repeatCount="indefinite" 
                    />
                  </circle>
                )}
              </g>
            );
          })}

          {AGENTS.map(agent => (
            <AgentNode key={agent.key} agent={agent} status={getStatus(agent.key)} />
          ))}
        </svg>
      </div>
      
      {/* Légende */}
      <div className="p-4 border-t border-white/5 flex gap-4 text-[10px] text-gray-500 justify-center">
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-700" /> Attente</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500" /> En cours</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> Terminé</div>
      </div>
    </div>
  );
}