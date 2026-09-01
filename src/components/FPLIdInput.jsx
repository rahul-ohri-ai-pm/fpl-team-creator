import { useState } from 'react'
import { Loader2, AlertCircle } from 'lucide-react'

export default function FPLIdInput({ onAnalysis }) {
  const [managerId, setManagerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!managerId.trim()) {
      setError('Please enter a valid FPL manager ID')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/fetch-team', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manager_id: parseInt(managerId) })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Manager not found')
      }

      const teamData = await response.json()
      onAnalysis(teamData)
    } catch (err) {
      setError(err.message || 'Failed to fetch team. Check your manager ID and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          FPL Manager ID
        </label>
        <input
          type="number"
          value={managerId}
          onChange={(e) => {
            setManagerId(e.target.value)
            setError(null)
          }}
          placeholder="e.g., 12345678"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-fpl-primary"
        />
        <p className="text-xs text-gray-500 mt-2">
          Find your manager ID in FPL → My Team → edit profile (URL: fantasy.premierleague.com/entry/YOUR_ID)
        </p>
      </div>

      {error && (
        <div className="flex gap-3 bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={!managerId || loading}
        className="btn-primary w-full"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
            Fetching...
          </>
        ) : (
          'Analyze Your Team'
        )}
      </button>
    </form>
  )
}
