import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { AccountCreationPage } from './pages/AccountCreationPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/register" element={<AccountCreationPage />} />
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
        {/* Placeholder for diagnostic - will be implemented in Story 3.6 */}
        <Route
          path="/diagnostic"
          element={
            <div className="min-h-screen bg-cream flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-charcoal">Diagnostic Assessment</h1>
                <p className="mt-2 text-charcoal/70">Coming soon...</p>
              </div>
            </div>
          }
        />
        {/* Placeholder for terms - static page */}
        <Route
          path="/terms"
          element={
            <div className="min-h-screen bg-cream flex items-center justify-center px-4">
              <div className="max-w-2xl text-center">
                <h1 className="text-2xl font-bold text-charcoal">Terms of Service</h1>
                <p className="mt-4 text-charcoal/70">Terms of Service content will be added here.</p>
              </div>
            </div>
          }
        />
        {/* Placeholder for privacy - static page */}
        <Route
          path="/privacy"
          element={
            <div className="min-h-screen bg-cream flex items-center justify-center px-4">
              <div className="max-w-2xl text-center">
                <h1 className="text-2xl font-bold text-charcoal">Privacy Policy</h1>
                <p className="mt-4 text-charcoal/70">Privacy Policy content will be added here.</p>
              </div>
            </div>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
