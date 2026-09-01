import { AlertCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function ErrorScreen({ error }) {
  const navigate = useNavigate()

  const getErrorMessage = (error) => {
    if (typeof error === 'string') {
      if (error.includes('not found')) return 'Manager not found. Check your ID and try again.'
      if (error.includes('screenshot')) return 'Couldn\'t read the screenshot. Try uploading a clearer image or enter manually.'
      if (error.includes('illegal')) return 'This squad breaks FPL rules. Please adjust and try again.'
      if (error.includes('network')) return 'Couldn\'t reach FPL data. Check your connection and retry.'
      return error
    }
    return 'Something went wrong. Please try again.'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center py-8">
      <div className="max-w-2xl mx-auto px-4 w-full">
        <div className="card text-center space-y-6 border-2 border-red-200">
          <div className="flex justify-center">
            <AlertCircle className="w-12 h-12 text-red-600" />
          </div>

          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Analysis failed
            </h2>
            <p className="text-lg text-red-700 mb-2">
              {getErrorMessage(error)}
            </p>
            <p className="text-gray-600">
              Please check your input and try again
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => navigate('/')}
              className="btn-primary flex-1"
            >
              Back to home
            </button>
            <button
              onClick={() => window.location.reload()}
              className="btn-secondary flex-1"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
