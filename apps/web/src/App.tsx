import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Placeholder for onboarding - will be implemented in Story 3.2 */}
        <Route
          path="/onboarding"
          element={
            <div className="min-h-screen bg-cream flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-charcoal">Onboarding</h1>
                <p className="mt-2 text-charcoal/70">Coming soon...</p>
              </div>
            </div>
          }
        />
        {/* Placeholder for login - will be implemented in Story 1.4 */}
        <Route
          path="/login"
          element={
            <div className="min-h-screen bg-cream flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-charcoal">Login</h1>
                <p className="mt-2 text-charcoal/70">Coming soon...</p>
              </div>
            </div>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
