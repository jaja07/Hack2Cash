/**
 * components/ChatInput.jsx
 * Text input + file attachment + send button.
 */
import { useState, useRef } from 'react'

export default function ChatInput({ onSend, onFile, disabled }) {
  const [text, setText]     = useState('')
  const fileRef             = useRef(null)

  const handleSend = () => {
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = (e) => {
    const file = e.target.files?.[0]
    if (file) onFile?.(file)
    e.target.value = ''
  }

  return (
    <div className="border-t border-gray-800 bg-gray-900 px-4 py-3">
      <div className="max-w-3xl mx-auto flex items-end gap-2">

        {/* File attach */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          title="Joindre un fichier CRA"
          className="p-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition disabled:opacity-40"
        >
          📎
        </button>
        <input ref={fileRef} type="file" className="hidden"
          accept=".pdf,.docx,.xlsx,.csv,.json,.txt" onChange={handleFile} />

        {/* Textarea */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Send a message or ask a question about your Activity Report."
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm
                     text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1
                     focus:ring-brand-500 transition scrollbar-thin max-h-40 leading-relaxed disabled:opacity-50"
          style={{ minHeight: '44px' }}
          onInput={(e) => {
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
          }}
        />

        {/* Send */}
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white transition
                     disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          title="Envoyer (Entrée)"
        >
          <svg className="w-5 h-5 rotate-90" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
          </svg>
        </button>
      </div>

      <p className="text-center text-gray-700 text-xs mt-2">
        Accepted formats : PDF · DOCX · XLSX · CSV · JSON · TXT &nbsp;·&nbsp; Send input
      </p>
    </div>
  )
}
