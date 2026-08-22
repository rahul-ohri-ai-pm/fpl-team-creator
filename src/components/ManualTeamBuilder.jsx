import { useState, useEffect } from 'react'
import { Loader2, AlertCircle, ChevronDown } from 'lucide-react'

const POSITIONS = ['GK', 'DEF', 'MID', 'FWD']
const QUOTA = { GK: 2, DEF: 5, MID: 5, FWD: 3 }

export default function ManualTeamBuilder({ onAnalysis }) {
  const [squad, setSquad] = useState({ GK: [], DEF: [], MID: [], FWD: [] })
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [activePosition, setActivePosition] = useState('GK')
  const [budget, setBudget] = useState(100.0)

  useEffect(() => {
    fetchPlayers()
  }, [])

  const fetchPlayers = async () => {
    setSearchLoading(true)
    try {
      const response = await fetch('/api/players')
      if (!response.ok) throw new Error('Failed to load players')
      const data = await response.json()
      setPlayers(data)
    } catch (err) {
      setError('Could not load player list')
    } finally {
      setSearchLoading(false)
    }
  }

  const getFilteredPlayers = () => {
    return players
      .filter(p => p.position === activePosition)
      .filter(p => {
        const isSelected = Object.values(squad).flat().some(s => s.id === p.id)
        return !isSelected && p.name.toLowerCase().includes(searchText.toLowerCase())
      })
      .sort((a, b) => a.price - b.price)
  }

  const addPlayer = (player) => {
    const position = player.position
    if (squad[position].length >= QUOTA[position]) {
      setError(`Max ${QUOTA[position]} ${position}s allowed`)
      return
    }

    const newSquad = { ...squad, [position]: [...squad[position], player] }
    setSquad(newSquad)
    setBudget(budget - player.price / 10)
    setSearchText('')
  }

  const removePlayer = (position, playerId) => {
    const player = squad[position].find(p => p.id === playerId)
    if (!player) return

    const newSquad = {
      ...squad,
      [position]: squad[position].filter(p => p.id !== playerId)
    }
    setSquad(newSquad)
    setBudget(budget + player.price / 10)
  }

  const handleSubmit = async () => {
    const totalPlayers = Object.values(squad).reduce((sum, pos) => sum + pos.length, 0)
    if (totalPlayers !== 15) {
      setError(`Please select 15 players (${totalPlayers} selected)`)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          squad: squad,
          bank: budget,
          free_transfers: 1
        })
      })

      if (!response.ok) throw new Error('Analysis failed')

      const data = await response.json()
      onAnalysis(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredPlayers = getFilteredPlayers()
  const totalPlayers = Object.values(squad).reduce((sum, pos) => sum + pos.length, 0)

  return (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {/* Squad Summary */}
      <div className="grid grid-cols-5 gap-2 bg-gray-50 p-4 rounded-lg">
        {POSITIONS.map(pos => (
          <div key={pos} className="text-center">
            <div className="font-semibold text-lg text-fpl-primary">{squad[pos].length}</div>
            <div className="text-xs text-gray-600">{pos}</div>
            <div className="text-xs text-gray-400">/{QUOTA[pos]}</div>
          </div>
        ))}
        <div className="text-center border-l border-gray-300">
          <div className={`font-semibold text-lg ${budget >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            £{budget.toFixed(1)}m
          </div>
          <div className="text-xs text-gray-600">Bank</div>
        </div>
      </div>

      {error && (
        <div className="flex gap-3 bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Position Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {POSITIONS.map(pos => (
          <button
            key={pos}
            onClick={() => { setActivePosition(pos); setSearchText('') }}
            className={`px-4 py-2 font-semibold ${activePosition === pos ? 'border-b-2 border-fpl-primary text-fpl-primary' : 'text-gray-600'}`}
          >
            {pos} ({squad[pos].length}/{QUOTA[pos]})
          </button>
        ))}
      </div>

      {/* Player Search */}
      <div>
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder={`Search ${activePosition} players...`}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-fpl-primary"
        />
      </div>

      {/* Selected Players */}
      {squad[activePosition].length > 0 && (
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-blue-700 mb-2">Selected:</p>
          <div className="flex flex-wrap gap-2">
            {squad[activePosition].map(player => (
              <div
                key={player.id}
                className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-blue-200 text-sm"
              >
                <span className="font-semibold">{player.name}</span>
                <span className="text-xs text-gray-600">£{(player.price / 10).toFixed(1)}m</span>
                <button
                  onClick={() => removePlayer(activePosition, player.id)}
                  className="text-red-600 hover:text-red-700 font-bold"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Players */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-gray-600">Available ({filteredPlayers.length}):</p>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {searchLoading ? (
            <div className="text-center py-4 text-gray-500">
              <Loader2 className="w-4 h-4 inline animate-spin" />
            </div>
          ) : filteredPlayers.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No players available</p>
          ) : (
            filteredPlayers.map(player => (
              <button
                key={player.id}
                onClick={() => addPlayer(player)}
                className="w-full text-left p-2 hover:bg-gray-100 rounded text-sm border border-gray-200"
              >
                <div className="font-semibold text-gray-900">{player.name}</div>
                <div className="text-xs text-gray-600">{player.team} • £{(player.price / 10).toFixed(1)}m</div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Analyze Button */}
      <button
        onClick={handleSubmit}
        disabled={totalPlayers !== 15 || loading}
        className="btn-primary w-full mt-4"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          `Analyze Squad (${totalPlayers}/15)`
        )}
      </button>
    </div>
  )
}
