import { ChevronDown, AlertCircle, CheckCircle2 } from 'lucide-react'

function getConfidenceColor(confidence) {
  if (confidence >= 80) return 'bg-confidence-high text-white'
  if (confidence >= 60) return 'bg-confidence-medium text-white'
  return 'bg-confidence-low text-white'
}

export default function RecommendationCard({ recommendation, expanded, onExpand }) {
  if (!recommendation) return null

  const { player_out, player_in, projected_points, confidence, why_bullets, risk } = recommendation

  return (
    <div className="card border-2 border-fpl-primary">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">YOUR BEST MOVE</h3>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <p className="text-sm text-gray-600">Transfer out</p>
            <p className="font-semibold text-gray-900">{player_out.name}</p>
            <p className="text-xs text-gray-500">{player_out.team}</p>
          </div>
          <div className="text-2xl text-gray-400">→</div>
          <div className="flex-1">
            <p className="text-sm text-gray-600">Transfer in</p>
            <p className="font-semibold text-gray-900">{player_in.name}</p>
            <p className="text-xs text-gray-500">{player_in.team}</p>
          </div>
        </div>
      </div>

      {/* Impact & Confidence */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-xs text-gray-600 mb-1">Projected impact</p>
          <p className="text-2xl font-bold text-green-600">+{projected_points.toFixed(1)} pts</p>
          <p className="text-xs text-gray-500">over 6 gameweeks</p>
        </div>
        <div className={`rounded-lg p-3 ${getConfidenceColor(confidence)}`}>
          <p className="text-xs opacity-90 mb-1">Confidence</p>
          <p className="text-2xl font-bold">{confidence}%</p>
          <p className="text-xs opacity-75">Model certainty</p>
        </div>
      </div>

      {/* Why Bullets */}
      <div className="mb-4 space-y-2">
        <p className="text-sm font-semibold text-gray-900">Why this transfer</p>
        <ul className="space-y-2">
          {why_bullets.map((bullet, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">{bullet}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Risk */}
      {risk && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-red-700">Main downside</p>
            <p className="text-sm text-red-700">{risk}</p>
          </div>
        </div>
      )}

      {/* Expand Details */}
      <button
        onClick={onExpand}
        className="text-sm font-semibold text-fpl-primary hover:text-blue-700 flex items-center gap-2 mb-4"
      >
        <span>{expanded ? 'Hide details' : 'Show details'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {expanded && (
        <div className="border-t border-gray-200 pt-4 space-y-3 text-sm">
          <div>
            <p className="font-semibold text-gray-900 mb-1">Fixtures (Next 6 GWs)</p>
            <p className="text-gray-700">{recommendation.fixture_analysis}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-900 mb-1">Expected Goal Involvements (xGI)</p>
            <p className="text-gray-700">{recommendation.xgi_explanation}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-900 mb-1">Minutes & Rotation Risk</p>
            <p className="text-gray-700">{recommendation.minutes_analysis}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-900 mb-1">Ownership</p>
            <p className="text-gray-700">{recommendation.ownership_note}</p>
          </div>
        </div>
      )}

      {/* CTAs */}
      <div className="flex gap-3 mt-6">
        <button className="btn-confirmation flex-1">
          ✓ Make this move
        </button>
        <button className="btn-secondary flex-1">
          ⚙️ More options
        </button>
      </div>
    </div>
  )
}
