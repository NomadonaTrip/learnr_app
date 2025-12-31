import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { AccountCreationPage } from './pages/AccountCreationPage'
import { LoginPage } from './pages/LoginPage'
import { DiagnosticPage } from './pages/DiagnosticPage'
import { DiagnosticResultsPage } from './pages/DiagnosticResultsPage'
import { QuizPage } from './pages/QuizPage'
import { ReadingLibraryPage } from './pages/ReadingLibraryPage'
import { ReadingDetailPage } from './pages/ReadingDetailPage'
import { useAuthStore } from './stores/authStore'

/** Route guard that redirects to login if not authenticated */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

/** Placeholder pages */
function ForgotPasswordPlaceholder() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-charcoal">Forgot Password</h1>
        <p className="mt-2 text-charcoal/70">Password recovery coming soon...</p>
      </div>
    </div>
  )
}


function TermsPlaceholder() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-2xl font-bold text-charcoal">Terms of Service</h1>
        <p className="mt-4 text-charcoal/70">Terms of Service content will be added here.</p>
      </div>
    </div>
  )
}

function PrivacyPlaceholder() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-2xl font-bold text-charcoal">Privacy Policy</h1>
        <p className="mt-4 text-charcoal/70">Privacy Policy content will be added here.</p>
      </div>
    </div>
  )
}


function StudyPlanPlaceholder() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-2xl font-bold text-charcoal">Study Plan</h1>
        <p className="mt-4 text-charcoal/70">Personalized study plan coming soon...</p>
      </div>
    </div>
  )
}

/** Data router configuration - required for useBlocker hook */
const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/onboarding', element: <OnboardingPage /> },
  { path: '/register', element: <AccountCreationPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/forgot-password', element: <ForgotPasswordPlaceholder /> },
  {
    path: '/diagnostic',
    element: (
      <ProtectedRoute>
        <DiagnosticPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/diagnostic/results',
    element: (
      <ProtectedRoute>
        <DiagnosticResultsPage />
      </ProtectedRoute>
    ),
  },
  { path: '/terms', element: <TermsPlaceholder /> },
  { path: '/privacy', element: <PrivacyPlaceholder /> },
  {
    path: '/quiz',
    element: (
      <ProtectedRoute>
        <QuizPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/study-plan',
    element: (
      <ProtectedRoute>
        <StudyPlanPlaceholder />
      </ProtectedRoute>
    ),
  },
  {
    path: '/reading-library',
    element: (
      <ProtectedRoute>
        <ReadingLibraryPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/reading-library/:queueId',
    element: (
      <ProtectedRoute>
        <ReadingDetailPage />
      </ProtectedRoute>
    ),
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
