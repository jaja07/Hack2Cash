/**
 * components/FileDropZone.jsx
 * Drag-and-drop file uploader.
 */
import { useState, useRef } from 'react'

const ACCEPT = ['.pdf', '.docx', '.xlsx', '.csv', '.json', '.txt']

export default function FileDropZone({ onFile, uploading }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  const handleChange = (e) => {
    const file = e.target.files?.[0]
    if (file) onFile(file)
    e.target.value = ''
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all
        ${dragOver
          ? 'border-brand-500 bg-brand-900/20'
          : 'border-gray-700 hover:border-gray-600 bg-gray-800/30 hover:bg-gray-800/50'
        }
        ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <input ref={inputRef} type="file" accept={ACCEPT.join(',')} className="hidden" onChange={handleChange} />
      <div className="text-4xl mb-3">{uploading ? '⏳' : '📂'}</div>
      <p className="text-gray-300 font-medium text-sm">
        {uploading ? 'Chargement en cours…' : 'Glissez votre CRA ici ou cliquez pour sélectionner'}
      </p>
      <p className="text-gray-600 text-xs mt-2">{ACCEPT.join(' · ')}</p>
    </div>
  )
}
