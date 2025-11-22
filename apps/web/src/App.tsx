import { BrowserRouter as Router } from 'react-router-dom'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-4xl font-bold text-gray-900">
            Welcome to LearnR
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            AI-Powered Adaptive Learning Platform for Professional Certification Exam Preparation
          </p>
        </div>
      </div>
    </Router>
  )
}

export default App
