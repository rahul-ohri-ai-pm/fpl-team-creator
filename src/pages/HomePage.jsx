import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ScreenshotUpload from '../components/ScreenshotUpload'
import FPLIdInput from '../components/FPLIdInput'
import ManualTeamBuilder from '../components/ManualTeamBuilder'
import { Upload, Hash, Hammer2 } from 'lucide-react'

export default function HomePage({ setAnalysisData, setLoading, setError }) {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState(null)

  const handleAnalysis = async (teamData) => {
    setLoading(true)
    setError(null)
    try {
      // Call backend engine with team data
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(teamData)
      })

      if (!response.ok) throw new Error('Analysis failed')

      const data = await response.json()
      setAnalysisData(data)
      navigate(`/team/${data.team_id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-2xl mx-auto px-4 py-8 md:py-16">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Know your next FPL move
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            See what to transfer. Understand why. Decide.
          </p>
          <p className="text-sm text-gray-500">
            Analyze your team in seconds • 87% average confidence • No signup required
          </p>
        </div>

        {/* Input Methods */}
        <div className="space-y-4">
          {/* Screenshot Upload */}
          <button
            onClick={() => setActiveTab(activeTab === 'screenshot' ? null : 'screenshot')}
            className="w-full p-6 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border-2 border-transparent hover:border-fpl-primary"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-fpl-primary/10 rounded-lg">
                <Upload className="w-6 h-6 text-fpl-primary" />
              </div>
              <div className="text-left flex-1">
                <h3 className="font-semibold text-gray-900">📸 Upload screenshot</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Take a screenshot of your squad and we'll analyze it instantly
                </p>
              </div>
            </div>
          </button>

          {activeTab === 'screenshot' && (
            <div className="bg-white rounded-lg shadow p-6 -mt-2 border-t-2 border-fpl-primary">
              <ScreenshotUpload onAnalysis={handleAnalysis} />
            </div>
          )}

          {/* FPL ID Input */}
          <button
            onClick={() => setActiveTab(activeTab === 'fpl-id' ? null : 'fpl-id')}
            className="w-full p-6 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border-2 border-transparent hover:border-fpl-primary"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-fpl-primary/10 rounded-lg">
                <Hash className="w-6 h-6 text-fpl-primary" />
              </div>
              <div className="text-left flex-1">
                <h3 className="font-semibold text-gray-900">Analyze by FPL ID</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Enter your FPL manager ID to fetch and analyze your live team
                </p>
              </div>
            </div>
          </button>

          {activeTab === 'fpl-id' && (
            <div className="bg-white rounded-lg shadow p-6 -mt-2 border-t-2 border-fpl-primary">
              <FPLIdInput onAnalysis={handleAnalysis} />
            </div>
          )}

          {/* Manual Team Builder */}
          <button
            onClick={() => setActiveTab(activeTab === 'manual' ? null : 'manual')}
            className="w-full p-6 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border-2 border-transparent hover:border-fpl-primary"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-fpl-primary/10 rounded-lg">
                <Hammer2 className="w-6 h-6 text-fpl-primary" />
              </div>
              <div className="text-left flex-1">
                <h3 className="font-semibold text-gray-900">Build team manually</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Select 15 players to create a custom squad for analysis
                </p>
              </div>
            </div>
          </button>

          {activeTab === 'manual' && (
            <div className="bg-white rounded-lg shadow p-6 -mt-2 border-t-2 border-fpl-primary">
              <ManualTeamBuilder onAnalysis={handleAnalysis} />
            </div>
          )}
        </div>

        {/* Trust Signals */}
        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-fpl-primary">87%</div>
            <p className="text-sm text-gray-600">Avg Confidence</p>
          </div>
          <div>
            <div className="text-2xl font-bold text-fpl-primary">&lt;3s</div>
            <p className="text-sm text-gray-600">To Recommend</p>
          </div>
          <div>
            <div className="text-2xl font-bold text-fpl-primary">∞</div>
            <p className="text-sm text-gray-600">Free Analysis</p>
          </div>
        </div>
      </div>
    </div>
  )
}
