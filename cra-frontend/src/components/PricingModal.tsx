import React from 'react';

const PLANS = [
  {
    name: 'Free',
    price: '€0',
    unit: '/month',
    features: ['3 analyses per day', 'CSV & TXT formats only', 'JSON + Markdown output', 'Community support', '1 saved agent profile'],
    color: 'border-gray-700'
  },
  {
    name: 'Standard',
    price: '€29',
    unit: '/month',
    features: ['Unlimited analyses', 'All formats (PDF, Excel, XML...)', 'All output formats incl. PPTX', 'Priority support', '5 saved agent profiles', 'BI connector (read)'],
    recommended: true,
    color: 'border-brand-500'
  },
  {
    name: 'Corporate',
    price: '€199',
    unit: '/month',
    features: ['Full Standard offer', 'API access + webhooks', 'Full BI integration (write)', 'Dedicated support SLA', 'Unlimited agent profiles', 'Custom domain training'],
    color: 'border-purple-500'
  }
];

export default function PricingModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-gray-900 border border-gray-800 rounded-3xl w-full max-w-5xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-gray-800 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white tracking-tight">PRICING PLANS</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors">✕</button>
        </div>
        
        <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div key={plan.name} className={`relative p-6 rounded-2xl border-2 bg-gray-800/50 flex flex-col ${plan.color}`}>
              {plan.recommended && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white text-black text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest">
                  Recommended
                </div>
              )}
              <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-3xl font-extrabold text-white">{plan.price}</span>
                <span className="text-gray-400 text-sm">{plan.unit}</span>
              </div>
              <ul className="space-y-3 flex-1 mb-8">
                {plan.features.map((feat) => (
                  <li key={feat} className="flex items-start gap-2 text-xs text-gray-300">
                    <span className="text-brand-400">✓</span> {feat}
                  </li>
                ))}
              </ul>
              <button className={`w-full py-3 rounded-xl font-bold text-sm transition-all ${plan.recommended ? 'bg-brand-600 text-white hover:bg-brand-700 shadow-lg shadow-brand-900/20' : 'bg-gray-700 text-gray-200 hover:bg-gray-600'}`}>
                Choose Plan
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}