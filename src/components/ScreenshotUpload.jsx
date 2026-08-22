import { useState } from 'react'
import { Upload, Loader2 } from 'lucide-react'

export default function ScreenshotUpload({ onAnalysis }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setError(null)

      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => setPreview(e.target?.result)
      reader.readAsDataURL(selected)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('screenshot', file)

      const response = await fetch('/api/ocr-screenshot', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to parse screenshot')
      }

      const teamData = await response.json()
      onAnalysis(teamData)
    } catch (err) {
      setError(err.message || 'Could not parse screenshot. Try a clearer image or enter manually.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-fpl-primary transition-colors cursor-pointer" onClick={() => document.getElementById('screenshot-input').click()}>
        <input
          id="screenshot-input"
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />

        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="font-semibold text-gray-900">
          {file ? 'Screenshot selected' : 'Upload your squad screenshot'}
        </p>
        <p className="text-sm text-gray-600 mt-1">
          PNG, JPG, or WebP • Any resolution
        </p>
      </div>

      {preview && (
        <div className="relative">
          <img
            src={preview}
            alt="Preview"
            className="w-full h-auto rounded-lg border border-gray-200 max-h-96 object-contain"
          />
          <button
            onClick={() => {
              setFile(null)
              setPreview(null)
            }}
            className="absolute top-2 right-2 bg-red-500 text-white rounded px-3 py-1 text-sm hover:bg-red-600"
          >
            Clear
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="btn-primary w-full"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          'Analyze Screenshot'
        )}
      </button>
    </div>
  )
}
