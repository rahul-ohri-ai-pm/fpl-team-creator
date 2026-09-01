import { Loader2 } from 'lucide-react'

export default function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center py-8">
      <div className="max-w-2xl mx-auto px-4 w-full">
        <div className="card text-center space-y-6">
          <div className="flex justify-center">
            <Loader2 className="w-12 h-12 text-fpl-primary animate-spin" />
          </div>

          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Analyzing your team...
            </h2>
            <p className="text-gray-600">
              We're crunching the numbers and running projections
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-gray-600">
              <span className="inline-block w-2 h-2 bg-fpl-primary rounded-full animate-pulse"></span>
              <span>Fetching team data</span>
            </div>
            <div className="flex items-center gap-3 text-gray-600">
              <span className="inline-block w-2 h-2 bg-fpl-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></span>
              <span>Calculating projections</span>
            </div>
            <div className="flex items-center gap-3 text-gray-600">
              <span className="inline-block w-2 h-2 bg-fpl-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></span>
              <span>Generating recommendation</span>
            </div>
          </div>

          <p className="text-sm text-gray-500">
            Usually takes less than 3 seconds
          </p>
        </div>
      </div>
    </div>
  )
}
