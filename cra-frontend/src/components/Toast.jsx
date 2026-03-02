// src/components/Toast.jsx
import React, { useEffect } from 'react';

export default function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000); // Disparaît après 3 secondes
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-600' : 'bg-red-600';

  return (
    <div className={`fixed top-5 right-5 z-50 ${bgColor} text-white px-6 py-3 rounded-lg shadow-2xl animate-in slide-in-from-right duration-300 flex items-center gap-3`}>
      <span>{type === 'success' ? '✅' : '❌'}</span>
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}