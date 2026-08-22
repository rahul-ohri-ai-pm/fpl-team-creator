import { useState } from 'react'
import TeamRatingCard from '../components/TeamRatingCard'
import RecommendationCard from '../components/RecommendationCard'
import AlternativesPanel from '../components/AlternativesPanel'
import KeepTeamOption from '../components/KeepTeamOption'
import LoadingScreen from '../components/LoadingScreen'
import ErrorScreen from '../components/ErrorScreen'

export default function AnalysisPage({ analysisData, loading, error }) {
  const [expandedCard, setExpandedCard] = useState(null)

  if (error) return <ErrorScreen error={error} />
  if (loading) return <LoadingScreen />
  if (!analysisData) return <ErrorScreen error="No analysis data available" />

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8">
      <div className="max-w-2xl mx-auto px-4 space-y-6">
        {/* Team Rating */}
        <TeamRatingCard
          score={analysisData.team_rating}
          summary={analysisData.biggest_problem}
          positions={analysisData.position_breakdown}
        />

        {/* Primary Recommendation */}
        <RecommendationCard
          recommendation={analysisData.recommendation}
          expanded={expandedCard === 'primary'}
          onExpand={() => setExpandedCard(expandedCard === 'primary' ? null : 'primary')}
        />

        {/* Alternatives */}
        {analysisData.alternatives?.length > 0 && (
          <AlternativesPanel
            alternatives={analysisData.alternatives}
            expanded={expandedCard === 'alternatives'}
            onExpand={() => setExpandedCard(expandedCard === 'alternatives' ? null : 'alternatives')}
          />
        )}

        {/* Keep Team Option */}
        <KeepTeamOption
          teamScore={analysisData.team_rating}
          reasoning={analysisData.keep_reasoning}
        />

        {/* Share Button */}
        <div className="card text-center">
          <button className="btn-primary">
            Share your analysis
          </button>
        </div>
      </div>
    </div>
  )
}
