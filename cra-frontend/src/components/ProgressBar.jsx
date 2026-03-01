/**
 * components/ProgressBar.jsx
 * Animated progress bar for job status.
 */
export default function ProgressBar({ progress = 0, label = '' }) {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>{label}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>
    </div>
  )
}
