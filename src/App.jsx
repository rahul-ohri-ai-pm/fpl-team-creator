import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import AnalysisPage from './pages/AnalysisPage'
import TeamPage from './pages/TeamPage'
import './index.css'

function App() {
  const [analysisData, setAnalysisData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage setAnalysisData={setAnalysisData} setLoading={setLoading} setError={setError} />} />
        <Route path="/analyze" element={<AnalysisPage analysisData={analysisData} loading={loading} error={error} />} />
        <Route path="/team/:teamId" element={<TeamPage />} />
      </Routes>
    </Router>
  )
}

export default App
