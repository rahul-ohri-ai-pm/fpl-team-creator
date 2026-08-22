import { ChevronDown } from 'lucide-react'

function getConfidenceBadgeColor(confidence) {
  if (confidence >= 80) return 'bg-confidence-high text-white'
  if (confidence >= 60) return 'bg-confidence-medium text-white'
  return 'bg-confidence-low text-white'
}

export default function AlternativesPanel({ alternatives, expanded, onExpand }) {
  if (!alternatives || alternatives.length === 0) return null

  return (
    <div className="card">
      <button
        onClick={onExpand}
        className="w-full flex items-center justify-between mb-4"
      >
        <h3 className="text-lg font-semibold text-gray-900">OTHER OPTIONS</h3>
        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {expanded && (
        <div className="space-y-3">
          {alternatives.map((alt, idx) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{idx + 2}. Option</p>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{alt.player_out.name}</span>
                    <span className="text-gray-400">→</span>
                    <span className="font-semibold text-gray-900">{alt.player_in.name}</span>
                  </div>
                </div>
                <span className={`confidence-badge ${getConfidenceBadgeColor(alt.confidence)}`}>
                  {alt.confidence}%
                </span>
              </div>

              <div className="flex items-center justify-between text-sm">
                <p className="text-gray-600">Projected impact</p>
                <p className="font-semibold text-green-600">+{alt.projected_points.toFixed(1)} pts</p>
              </div>

              <button className="mt-3 btn-secondary w-full text-sm">
                Use this instead
              </button>
            </div>
          ))}
        </div>
      )}

      {!expanded && (
        <div className="grid grid-cols-2 gap-3">
          {alternatives.slice(0, 2).map((alt, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-600 mb-1">{idx + 2}. {alt.player_in.name}</p>
              <p className="text-sm font-semibold text-gray-900">+{alt.projected_points.toFixed(1)}</p>
              <p className="text-xs text-gray-600">{alt.confidence}% confidence</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
