export default function KeepTeamOption({ teamScore, reasoning }) {
  return (
    <div className="card border-2 border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">KEEP YOUR TEAM?</h3>

      <div className="mb-4">
        <p className="text-gray-700 mb-3">
          This recommendation is strong, but holding is also valid if you prefer to:
        </p>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex gap-2">
            <span>•</span>
            <span>Bank the transfer for a future gameweek</span>
          </li>
          <li className="flex gap-2">
            <span>•</span>
            <span>Avoid taking hits on uncertain transfers</span>
          </li>
          <li className="flex gap-2">
            <span>•</span>
            <span>Wait for more fixture clarity</span>
          </li>
        </ul>
      </div>

      {reasoning && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 text-sm text-yellow-800">
          <strong>Why holding is reasonable:</strong> {reasoning}
        </div>
      )}

      <button className="btn-secondary w-full">
        ✓ Keep as-is
      </button>
    </div>
  )
}
