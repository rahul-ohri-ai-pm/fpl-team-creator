import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

export default function TeamRatingCard({ score, summary, positions }) {
  const [expanded, setExpanded] = useState(false)

  const getHealthStatus = (score) => {
    if (score >= 80) return { label: '💪 Strong', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' }
    if (score >= 60) return { label: '⚠️ Fair', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' }
    return { label: '🔴 Concerning', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
  }

  const status = getHealthStatus(score)

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">YOUR TEAM</h2>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600"
        >
          <ChevronDown className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
      </div>

      <div className="flex items-center gap-6 mb-4">
        <div className="text-center">
          <div className="relative w-24 h-24 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'}
                strokeWidth="8"
                strokeDasharray={`${(score / 100) * 282.7} 282.7`}
                className="transition-all"
              />
            </svg>
            <div className="absolute text-center">
              <div className="text-3xl font-bold text-gray-900">{Math.round(score)}</div>
              <div className="text-xs text-gray-600">/100</div>
            </div>
          </div>
        </div>

        <div className="flex-1">
          <p className={`text-lg font-semibold ${status.color}`}>{status.label}</p>
          <p className="text-sm text-gray-600 mt-2">
            <strong>Biggest concern:</strong> {summary}
          </p>
        </div>
      </div>

      {expanded && positions && (
        <div className="mt-6 pt-6 border-t border-gray-200 space-y-3">
          <h3 className="font-semibold text-gray-900 text-sm">Position Strength</h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(positions).map(([pos, score]) => (
              <div key={pos} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{pos}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className="font-semibold text-gray-900 w-8 text-right">{Math.round(score)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
